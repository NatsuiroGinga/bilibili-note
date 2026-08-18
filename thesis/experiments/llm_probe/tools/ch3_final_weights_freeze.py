# -*- coding: utf-8 -*-
"""第三章定稿模型权重固化（协议 A 四格重跑 + 逐位复现校验 + 归档打包）。

与 tools/ch3_2x2_fairsel.py 的**唯一**差异是「把选中 epoch 的权重存盘并从盘回载后评价」。
训练逻辑、选择规则、评价口径、全部超参逐字照抄，不做任何改动：
  - 模型 Model.agg / Model.lp、lp_pool、损失、pos_weight/spw 口径：逐字照抄。
  - 划分与自检：逐字照抄（RandomState(42) 排列、VAL_FRAC=0.10、TIME_TAIL=0.15）。
  - 训练循环：逐字照抄（20 epoch × 1000 步、BS=64、L=128、lr=2e-3、AdamW、clip 1.0、AUX_W=1.0）。
  - 选择规则：逐字照抄（LSPR23 实体不相交验证集逐流 AP 单 epoch argmax，无末 5 平均，不早停）。

新增（不触碰上述任何一项）：
  1. 选择冻结后，把每格选中 epoch 的 state_dict 写成 safetensors；
  2. 评价阶段不再直接用内存里的 state，而是**从盘回载 safetensors** 再评价，
     因此四格指标全部来自归档权重本身（评价次数仍为 4，隔离断言不变）；
  3. 三重验证：选中 epoch、C11 逐流分数（np.array_equal）、四格指标，逐位比对既有制品；
  4. 生成 config.json / metrics.json / manifest.json，并复制 inference.py 与 README.md。

============================ LSPR24 隔离保证（沿用既有机制）============================
  阶段一「选择」：进程内只从磁盘读入 LSPR23。train_and_select() 函数体内不出现任何 24 标识符。
  阶段闸门      ：selection_frozen.json 先落盘，再置 SELECTION_FROZEN = True。
  权重落盘      ：发生在阶段闸门之后、读入 LSPR24 之前（权重只由 LSPR23 决定）。
  阶段二「评价」：load24 与 score24 首行断言闸门；结束断言 _EVAL24_CALLS == 4、_N24_LOADS == 1。
=====================================================================================
"""

import hashlib
import json
import os
import platform
import shutil
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from safetensors.torch import load_file, save_file
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
REF = f"{ROOT}/runs/diagnostics/ch3-2x2-fairsel"          # 既有协议 A 制品，只读
OUT = f"{ROOT}/runs/diagnostics/ch3-final-weights"        # 本次归档根
ASSETS = f"{ROOT}/tools/ch3_final_weights_assets"         # inference.py / README.md 源
os.makedirs(OUT, exist_ok=True)

# ---- 超参：逐字照抄 ch3_2x2_fairsel.py 第 49-54 行 ----
L, BS, HID = 128, 64, 192
SEED, AUX_W = 42, 1.0
EPOCH_STEPS = 1000
N_EPOCH = 20
VAL_FRAC, TIME_TAIL = 0.10, 0.15
LR, WD_DECAY, WD_NODECAY, DROPOUT, CLIP = 2e-3, 0.01, 0.0, 0.1, 1.0

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0

CELLS = [("C00", False, False), ("C01", False, True),
         ("C10", True, False), ("C11", True, True)]
CELL_ROLE = {
    "C00": "基线：无因果前缀聚合、无 Lp 池化（逐流 MLP）",
    "C01": "仅 Lp 序列级池化（无因果前缀聚合）",
    "C10": "仅因果前缀聚合（无 Lp 池化）",
    "C11": "完整方法 CPA-ELP：因果前缀聚合 + Lp 序列级池化",
}

# ---- 既有制品（只读参照）----
REF_SEL = json.load(open(f"{REF}/selection_frozen.json"))
REF_RES = json.load(open(f"{REF}/ch3_2x2_fairsel_results.json"))
log("=" * 96)
log(f"参照制品已读入：{REF}/selection_frozen.json 与 {REF}/ch3_2x2_fairsel_results.json")
log("参照选中 epoch：" + "  ".join(
    f"{c}={REF_SEL['cells'][c]['selected_epoch']}" for c in ["C00", "C01", "C10", "C11"]))


def sha256_bytes(b):
    h = hashlib.sha256(); h.update(b); return h.hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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

rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut
tr_mask = ~(m_ent | m_time)
tr_idx = np.flatnonzero(tr_mask)
val_idx = np.flatnonzero(m_ent & ~m_time)
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
    """LSPR23 实体不相交验证集上的逐流 AP。唯一的模型选择信号来源。"""
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
    """训练 20 epoch 不早停，逐 epoch 用 LSPR23 验证 AP 选检查点。函数体内无任何 LSPR24 标识符。"""
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

# ---- 验证一：选中 epoch 与既有制品逐格比对 ----
V1 = {}
v1_all = True
for c in ["C00", "C01", "C10", "C11"]:
    ref_ep = REF_SEL["cells"][c]["selected_epoch"]
    ref_ap = REF_SEL["cells"][c]["val_ap_at_selected"]
    ref_p = REF_SEL["cells"][c]["p_at_selected"]
    ok_ep = int(SEL[c]["best"]["epoch"]) == int(ref_ep)
    ok_ap = float(SEL[c]["best"]["ap"]) == float(ref_ap)
    ok_p = float(SEL[c]["best"]["p"]) == float(ref_p)
    hist_ok = SEL[c]["hist"] == [[int(e), float(a), float(pp)]
                                 for e, a, pp in REF_SEL["cells"][c]["val_ap_history"]]
    V1[c] = {"selected_epoch_new": int(SEL[c]["best"]["epoch"]), "selected_epoch_ref": int(ref_ep),
             "epoch_match": bool(ok_ep), "val_ap_new": float(SEL[c]["best"]["ap"]),
             "val_ap_ref": float(ref_ap), "val_ap_bitwise_equal": bool(ok_ap),
             "p_new": float(SEL[c]["best"]["p"]), "p_ref": float(ref_p),
             "p_bitwise_equal": bool(ok_p),
             "full_val_ap_history_bitwise_equal": bool(hist_ok)}
    v1_all = v1_all and ok_ep and ok_ap and ok_p and hist_ok
    log(f"  验证一 {c}: epoch {SEL[c]['best']['epoch']} vs {ref_ep} "
        f"{'一致' if ok_ep else '不一致'} | 验证AP 逐位{'一致' if ok_ap else '不一致'} | "
        f"p 逐位{'一致' if ok_p else '不一致'} | 20epoch历史逐位{'一致' if hist_ok else '不一致'}")
log(f"验证一（选中 epoch）总体：{'通过' if v1_all else '不通过'}")

# ---- 权重落盘：仍在读入 LSPR24 之前，权重只由 LSPR23 决定 ----
log("=" * 96)
log("把每格选中 epoch 的权重写成 safetensors（发生在读入 LSPR24 之前）")
WPATH = {}
for cid, agg, lp in CELLS:
    d = f"{OUT}/{cid}"
    os.makedirs(d, exist_ok=True)
    tensors = {k: v.detach().cpu().contiguous() for k, v in SEL[cid]["best"]["state"].items()}
    meta = {"cell": cid, "aggregate_enabled": str(bool(agg)), "lp_enabled": str(bool(lp)),
            "selected_epoch": str(SEL[cid]["best"]["epoch"]), "seed": str(SEED),
            "protocol": "protocol-a-lspr23-entity-disjoint-val-single-epoch-argmax",
            "input_size": str(D), "hidden_size": str(HID), "sequence_length": str(L)}
    p = f"{d}/weights.safetensors"
    save_file(tensors, p, metadata=meta)
    WPATH[cid] = p
    log(f"  {cid} 已写 {p}  {os.path.getsize(p):,} 字节  张量 {len(tensors)} 个  参数 {SEL[cid]['npar']:,}")

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
log("阶段二 评价：首次读入 LSPR24（选择已冻结，权重已落盘）")
X24 = np.load(f"{CACHE}/X24.npy")
y24 = np.load(f"{CACHE}/y24.npy")
I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
t24 = np.load(f"{CACHE}/t24.npy")
assert X24.shape[1] == D

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
    """LSPR24 逐流打分。推理循环逐字照抄 ch3_2x2_fairsel.py 第 316-321 行。"""
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


REF_SCORES = np.load(f"{REF}/scores_C11.npy")
REF_SEEN = np.load(f"{REF}/seen_C11.npy")
log(f"既有 C11 逐流分数已读入：{REF_SCORES.shape} {REF_SCORES.dtype}")

RES = {}
V2 = None
ROUNDTRIP = {}
log("=" * 96)
log("每格从盘回载 safetensors 权重，在 LSPR24 上评价一次（评价所用权重即归档权重）")
for cid, agg, lp in CELLS:
    net = Model(agg, lp, HID).to(dev)
    disk_state = load_file(WPATH[cid], device=dev)
    # 回载前先证明盘上权重与内存中选中权重逐位一致
    mem_state = SEL[cid]["best"]["state"]
    assert set(disk_state.keys()) == set(mem_state.keys()), f"{cid} safetensors 张量名不匹配"
    rt = all(bool(torch.equal(disk_state[k], mem_state[k].to(dev))) for k in mem_state)
    ROUNDTRIP[cid] = {"tensor_names": sorted(mem_state.keys()), "bitwise_equal_to_memory": bool(rt)}
    assert rt, f"{cid} safetensors 往返不是逐位一致"
    net.load_state_dict(disk_state)
    p = net.p.item()
    assert abs(p - SEL[cid]["best"]["p"]) < 1e-9, f"{cid} 权重回载后 p 不一致"
    t1 = time.time()
    sc, seen = score24(net)
    ev_t = time.time() - t1
    fap = average_precision_score(y24[seen], sc[seen])
    fauc = roc_auc_score(y24[seen], sc[seen])
    e_max, n_ent_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, p if lp else None)
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
        f"DR@4%FPR={dr_main:.6f} (max口径={dr_max:.6f}) 覆盖实体={n_ent_ok:,} 推理{ev_t:.1f}秒")
    if cid == "C11":
        eq = bool(np.array_equal(sc, REF_SCORES))
        seen_eq = bool(np.array_equal(seen, REF_SEEN))
        allclose = bool(np.allclose(sc, REF_SCORES, rtol=1e-6, atol=1e-7))
        diff = np.abs(sc.astype(np.float64) - REF_SCORES.astype(np.float64))
        n_diff = int((sc != REF_SCORES).sum())
        V2 = {"scores_bitwise_equal": eq, "seen_bitwise_equal": seen_eq,
              "n_flows": int(sc.size), "n_differing_elements": n_diff,
              "max_abs_diff": float(diff.max()), "mean_abs_diff": float(diff.mean()),
              "np_allclose_rtol1e-6_atol1e-7": allclose,
              "sha256_new_scores_bytes": sha256_bytes(sc.tobytes()),
              "sha256_ref_scores_bytes": sha256_bytes(REF_SCORES.tobytes()),
              "ref_scores_path": f"{REF}/scores_C11.npy",
              "weights_used": WPATH["C11"]}
        log(f"  验证二 C11 逐流分数：np.array_equal={eq} seen逐位={seen_eq} "
            f"不同元素={n_diff:,}/{sc.size:,} 最大绝对差={diff.max():.3e}")
        np.save(f"{OUT}/scores_C11_reproduced.npy", sc)
    del sc, seen, net, disk_state
    torch.cuda.empty_cache()

assert _EVAL24_CALLS == 4, f"LSPR24 评价次数应为 4（每格一次），实为 {_EVAL24_CALLS}"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次（每格恰一次），均发生在选择冻结之后")

# ---- 验证三：四格指标逐位比对 ----
METRIC_KEYS = ["fap", "fauc", "e_max", "e_lp", "dr_main", "dr_max"]
V3 = {}
v3_all = True
log("=" * 96)
log("验证三 指标逐位比对（新 vs 既有 ch3_2x2_fairsel_results.json）")
for cid in ["C00", "C01", "C10", "C11"]:
    ref = REF_RES["cells"][cid]
    per = {}
    for k in METRIC_KEYS:
        eq = float(RES[cid][k]) == float(ref[k])
        per[k] = {"new": float(RES[cid][k]), "ref": float(ref[k]), "bitwise_equal": bool(eq),
                  "abs_diff": abs(float(RES[cid][k]) - float(ref[k]))}
        v3_all = v3_all and eq
    ent_eq = int(RES[cid]["n_ent_scored"]) == int(ref["n_ent_scored"])
    per["n_ent_scored"] = {"new": int(RES[cid]["n_ent_scored"]), "ref": int(ref["n_ent_scored"]),
                           "equal": bool(ent_eq)}
    v3_all = v3_all and ent_eq
    V3[cid] = per
    log(f"  {cid}: " + " ".join(
        f"{k}{'=' if per[k]['bitwise_equal'] else '≠'}" for k in METRIC_KEYS)
        + f"  覆盖实体{'一致' if ent_eq else '不一致'}")
    for k in METRIC_KEYS:
        log(f"     {k}: 新={per[k]['new']!r} 既有={per[k]['ref']!r} 差={per[k]['abs_diff']:.3e}")
log(f"验证三（指标逐位）总体：{'通过' if v3_all else '不通过'}")

TRIPLE = {"v1_selected_epoch_match": bool(v1_all),
          "v2_scores_bitwise_equal": bool(V2["scores_bitwise_equal"]) if V2 else False,
          "v3_metrics_bitwise_equal": bool(v3_all),
          "all_passed": bool(v1_all and V2 and V2["scores_bitwise_equal"] and v3_all),
          "detail_v1": V1, "detail_v2": V2, "detail_v3": V3,
          "safetensors_roundtrip": ROUNDTRIP,
          "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS}}
json.dump(TRIPLE, open(f"{OUT}/verification.json", "w"), ensure_ascii=False, indent=2)
log("=" * 96)
log(f"三重验证：一 选中epoch={'通过' if v1_all else '不通过'} | "
    f"二 C11分数逐位={'通过' if (V2 and V2['scores_bitwise_equal']) else '不通过'} | "
    f"三 指标逐位={'通过' if v3_all else '不通过'}")
json.dump({"cells": RES, "selection": _frozen["cells"], "verification": TRIPLE},
          open(f"{OUT}/rerun_results.json", "w"), ensure_ascii=False, indent=2)

if not TRIPLE["all_passed"]:
    log("三重验证未全过：按合同停止，不生成 manifest.json，不封包。")
    log(f"证据已保留：{OUT}/verification.json 与 {OUT}/rerun_results.json")
    sys.exit(9)

# =====================================================================================
# 归档打包
# =====================================================================================
log("=" * 96)
log("三重验证全过，开始生成归档包")
ENV = {"python": platform.python_version(), "torch": torch.__version__,
       "torch_cuda": torch.version.cuda, "numpy": np.__version__,
       "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
       "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
       "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
       "use_deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled())}
try:
    import safetensors as _st
    ENV["safetensors"] = _st.__version__
except Exception:
    ENV["safetensors"] = "unknown"
try:
    import sklearn as _sk
    ENV["scikit_learn"] = _sk.__version__
except Exception:
    ENV["scikit_learn"] = "unknown"

COMMON = {
    "schema_version": "ch3-protocol-a-final-weights-config-v1",
    "protocol": "协议A：LSPR23实体不相交验证集上逐epoch取逐流AP最大的单个epoch，无末5平均，不早停",
    "protocol_id": "protocol-a-lspr23-entity-disjoint-val-single-epoch-argmax",
    "source_script": "tools/ch3_2x2_fairsel.py（训练/选择/评价逐字照抄）",
    "freeze_script": "tools/ch3_final_weights_freeze.py",
    "seed": SEED,
    "architecture": {"input_size": D, "hidden_size": HID, "dropout": DROPOUT,
                     "sequence_length": L, "n_parameters": int(SEL["C11"]["npar"]),
                     "p_log_init": float(np.log(2.0)),
                     "p_clamp": [1e-3, 1e3],
                     "layers": "f=Linear(83,192)+ReLU+Dropout(0.1); "
                               "g=Linear(384,192)+ReLU+Dropout(0.1); o=Linear(192,1); p_log 标量"},
    "training": {"batch_size": BS, "sequence_length": L, "learning_rate": LR,
                 "optimizer": "AdamW", "weight_decay_decay_group": WD_DECAY,
                 "weight_decay_nodecay_group": WD_NODECAY,
                 "nodecay_params": "所有 .bias 与 p_log",
                 "grad_clip_norm": CLIP, "aux_loss_weight": AUX_W,
                 "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
                 "total_steps": N_EPOCH * EPOCH_STEPS,
                 "lr_scheduler": None, "early_stopping": False,
                 "flow_loss": "BCEWithLogitsLoss(reduction=none, pos_weight=逐流pos_weight)，掩码加权均值",
                 "sequence_aux_loss": "BCELoss(Lp池化后的序列概率, 序列标签)，正例权重 spw",
                 "flow_pos_weight": float(_pos.item()),
                 "sequence_spw": float(_spw),
                 "torch_manual_seed": SEED, "numpy_seed": SEED,
                 "batch_sampler_generator_seed": SEED,
                 "batch_sampler": "torch.Generator().manual_seed(42) 上的 torch.randint 有放回采样"},
    "data": {"cache_root": CACHE,
             "train_dataset": "LSPR23（全量缓存 X23/y23/I23/M23/E23/T23）",
             "eval_dataset": "LSPR24（X24/y24/I24/M24/s24/d24/t24）",
             "feature_count": D,
             "feature_contract": "Dijk 2026 附录 A 的 83 字段口径",
             "input_convention": "X 为缓存约定：先用 LSPR23 逐列均值/标准差标准化再裁剪到 [-10,10]，"
                                 "标准化统计量由 tools/select_signal.py 在建缓存时算出",
             "val_frac": VAL_FRAC, "time_tail": TIME_TAIL,
             "n_entity_lspr23": 150680, "n_train_seq": int(len(tr_idx)),
             "n_val_seq": int(len(val_idx)),
             "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                        "flow_pos_rate": _flow_pos, "entity_prior": float(ent_lab.mean())}},
    "environment": ENV,
    "research_only": True,
}

for cid, agg, lp in CELLS:
    cfg = dict(COMMON)
    cfg["cell"] = {"id": cid, "role": CELL_ROLE[cid],
                   "aggregate_enabled": bool(agg), "lp_enabled": bool(lp)}
    cfg["selected"] = {"epoch": int(SEL[cid]["best"]["epoch"]),
                       "step": int(SEL[cid]["best"]["epoch"]) * EPOCH_STEPS,
                       "val_ap_lspr23_entity_disjoint": float(SEL[cid]["best"]["ap"]),
                       "p_at_selected": float(SEL[cid]["best"]["p"]),
                       "val_ap_history": SEL[cid]["hist"]}
    cfg["weights_file"] = "weights.safetensors"
    cfg["state_dict_keys"] = ROUNDTRIP[cid]["tensor_names"]
    json.dump(cfg, open(f"{OUT}/{cid}/config.json", "w"), ensure_ascii=False, indent=2)

    met = {"schema_version": "ch3-protocol-a-final-weights-metrics-v1",
           "cell": cid, "role": CELL_ROLE[cid],
           "protocol_id": COMMON["protocol_id"],
           "eval_dataset": "LSPR24",
           "aggregation_for_entity_metrics": "Lp（本格 lp=True）" if lp else "max（本格 lp=False，Lp 退化为 max）",
           "flow_ap": RES[cid]["fap"], "flow_auc": RES[cid]["fauc"],
           "entity_ap_max": RES[cid]["e_max"], "entity_ap_lp": RES[cid]["e_lp"],
           "dr_at_4pct_fpr_main": RES[cid]["dr_main"], "dr_at_4pct_fpr_max": RES[cid]["dr_max"],
           "n_entity_scored": RES[cid]["n_ent_scored"],
           "p_at_selected": RES[cid]["p"],
           "selected_epoch": RES[cid]["sel_epoch"],
           "val_ap_lspr23_entity_disjoint": RES[cid]["val_ap"],
           "train_seconds": RES[cid]["tr"], "eval_seconds": RES[cid]["ev"],
           "lspr24": COMMON["data"]["lspr24"],
           "reference_ch3_2x2_fairsel": {k: float(REF_RES["cells"][cid][k]) for k in METRIC_KEYS},
           "bitwise_equal_to_reference": {k: V3[cid][k]["bitwise_equal"] for k in METRIC_KEYS},
           "note": "LSPR24 已在多轮人机循环中反复用于探索性评价，不是独立测试集；指标只供研究复核。"}
    json.dump(met, open(f"{OUT}/{cid}/metrics.json", "w"), ensure_ascii=False, indent=2)
    log(f"  {cid}: config.json 与 metrics.json 已写入 {OUT}/{cid}/")

for name in ["inference.py", "README.md"]:
    shutil.copyfile(f"{ASSETS}/{name}", f"{OUT}/{name}")
    log(f"  已复制 {name} 到 {OUT}/")

# 包内清单（不含 manifest.json 自身，也不含运行期日志与中间制品）
PKG_FILES = ["README.md", "inference.py"]
for cid, _, _ in CELLS:
    PKG_FILES += [f"{cid}/weights.safetensors", f"{cid}/config.json", f"{cid}/metrics.json"]
PKG_FILES = sorted(PKG_FILES)
files = []
total = 0
for rel in PKG_FILES:
    ap = f"{OUT}/{rel}"
    b = os.path.getsize(ap)
    total += b
    files.append({"path": rel, "bytes": b, "sha256": sha256_file(ap)})
MANIFEST = {
    "schema_version": "ch3-protocol-a-final-weights-manifest-v1",
    "package_name": "ch3-final-weights",
    "description": "第三章定稿模型（协议 A）四格权重归档",
    "protocol_id": COMMON["protocol_id"],
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "self_excluded": True,
    "file_count": len(files),
    "total_bytes": total,
    "files": files,
    "selected_epochs": {c: int(SEL[c]["best"]["epoch"]) for c in ["C00", "C01", "C10", "C11"]},
    "triple_verification": {
        "v1_selected_epoch_match": TRIPLE["v1_selected_epoch_match"],
        "v2_scores_bitwise_equal": TRIPLE["v2_scores_bitwise_equal"],
        "v3_metrics_bitwise_equal": TRIPLE["v3_metrics_bitwise_equal"],
        "all_passed": TRIPLE["all_passed"],
        "reference_run": REF,
        "v2_detail": {k: V2[k] for k in ["n_flows", "n_differing_elements", "max_abs_diff",
                                         "sha256_new_scores_bytes", "sha256_ref_scores_bytes"]},
    },
    "environment": ENV,
    "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS},
}
json.dump(MANIFEST, open(f"{OUT}/manifest.json", "w"), ensure_ascii=False, indent=2)
log(f"manifest.json 已写：{len(files)} 个文件，共 {total:,} 字节")
for f in files:
    log(f"  {f['sha256']}  {f['bytes']:>9,}  {f['path']}")
log(f"manifest.json 自身 SHA-256={sha256_file(f'{OUT}/manifest.json')}")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
