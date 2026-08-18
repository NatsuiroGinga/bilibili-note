# -*- coding: utf-8 -*-
"""诊断（不改变任何已冻结的选择，不触碰 LSPR24）：跨 L 排序是不是验证集口径漂移的产物。

ch3_valset_crossL_audit.py 已实测：三个 L 的验证**逐流集合**不同，正例率分别是
L=32 0.084154 / L=64 0.066945 / L=128 0.042499——相差约两倍。AP 随正例率上升，
所以「L=64/32 的配置验证 AP 普遍高于 L=128」这一现象，可能全部或部分来自口径差，
而不是模型更好。这是可证伪的，本脚本用实验判它，不用文字推演。

做法：
  一、从 ch3-hparam-fairsel-v2/selection_frozen.json 读出每个 L 按既定协议排名第一的配置。
  二、用完全相同的代码路径与 seed 重训这 3 个配置（同一 train_and_select 逻辑）。
      各自的「本 L 验证集 top-5 预测平均 AP」必须逐位复现主运行，否则本诊断作废。
  三、取三个 L 验证流集合的**公共交集**，在同一批流上重算三者的 top-5 预测平均 AP，
      得到正例率完全相同的可比排序。
  四、报告两种排序是否一致。

本脚本**不改变主运行已冻结的胜者**，也**不会**产生任何 LSPR24 数字：
SELECTION_FROZEN 恒为 False，guarded_load 对任何含 24 的数组一律断言失败。
不创建 SwanLab 运行身份。不落盘逐流分数。

注意：训练集也随 L 变化（同一时间尾部规则），本诊断只能统一**验证口径**，
无法统一训练口径；这一残余项在报告中显式标注，不得当作已消除。
"""

import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
MAIN = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-hparam-fairsel-v2"
SEED, BS, LR, DP = 42, 64, 2e-3, 0.1
EPOCH_STEPS, TOPK = 1000, 5
VAL_FRAC, TIME_TAIL = 0.10, 0.15
GRID_L = (32, 64, 128)

SELECTION_FROZEN = False          # 本脚本永不置真：LSPR24 在本进程内不可达


def guarded_load(name, allow_pickle=False):
    assert SELECTION_FROZEN or "24" not in name, f"本诊断禁止读入 {name}.npy"
    return np.load(f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


FROZEN = json.load(open(f"{MAIN}/selection_frozen.json"))
CFGS = FROZEN["hparam_configs"]
PICK = {}
for Lu in GRID_L:
    cand = [c for c in CFGS.values() if c["L"] == Lu]
    best = sorted(cand, key=lambda c: (-c["val_ap_pred_avg"], c["idx"]))[0]
    PICK[Lu] = best
    log(f"L={Lu:>3} 既定协议内排名第一：{best['name']} 本L验证AP={best['val_ap_pred_avg']:.8f} "
        f"top5epoch={best['topk_epochs']}")

X23 = guarded_load("X23"); y23 = guarded_load("y23")
e23f = guarded_load("ent23"); t23f = guarded_load("t23_flow")
D = X23.shape[1]
assert D == 83
dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda"
log(f"LSPR23 流={len(y23):,} 特征={D} | torch {torch.__version__}")

_ORD = np.lexsort((t23f, e23f))
_IV = e23f[_ORD]
_BND = np.flatnonzero(np.r_[True, _IV[1:] != _IV[:-1], True])
_SEGLEN = np.diff(_BND)
del _IV
_rs = np.random.RandomState(SEED)
_uent = np.unique(e23f)
_perm = _rs.permutation(len(_uent))
VAL_ENT = set(_uent[_perm[:max(1, int(len(_uent) * VAL_FRAC))]].tolist())
assert len(_uent) == 150680

PREP = {}
for Lu in GRID_L:
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
    Mu = Mb.astype(np.float32)
    EL, TL = e23f[_ORD[starts]], t23f[_ORD[starts]]
    m_ent = np.fromiter((e in VAL_ENT for e in EL), bool, len(EL))
    m_time = TL >= np.quantile(TL, 1.0 - TIME_TAIL)
    tr_idx = np.flatnonzero(~(m_ent | m_time))
    val_idx = np.flatnonzero(m_ent & ~m_time)
    sl = (y23[Iu.reshape(-1)].reshape(Iu.shape) * Mu).max(1) > 0
    spw = float((1 - sl.mean()) / max(sl.mean(), 1e-8))
    s_, r_ = starts[val_idx], real[val_idx]
    vpos = np.repeat(s_, r_) + (np.arange(r_.sum()) - np.repeat(np.cumsum(r_) - r_, r_))
    PREP[Lu] = {"I": Iu, "M": Mu, "tr": tr_idx, "val": val_idx, "spw": spw,
                "val_flows": _ORD[vpos],
                "n_epoch": FROZEN["per_L"][str(Lu)]["n_epoch"]}
    log(f"  L={Lu:>3} 序列 {n:,} 训练 {len(tr_idx):,} 验证 {len(val_idx):,} "
        f"验证流 {len(vpos):,} 正例率 {y23[_ORD[vpos]].mean():.6f} spw={spw:.4f} "
        f"轮数 {PREP[Lu]['n_epoch']}")
    del sl

# ---- 公共验证流集合：三个 L 的交集 ----
COMMON = PREP[GRID_L[0]]["val_flows"]
for Lu in GRID_L[1:]:
    COMMON = np.intersect1d(COMMON, PREP[Lu]["val_flows"], assume_unique=True)
IN_COMMON = np.zeros(len(y23), bool); IN_COMMON[COMMON] = True
log("=" * 100)
log(f"公共验证流集合：{len(COMMON):,} 条，正例 {int(y23[COMMON].sum()):,}，"
    f"正例率 {y23[COMMON].mean():.6f}（三个 L 完全相同，正例率不再有差）")
for Lu in GRID_L:
    log(f"  L={Lu:>3} 自身验证流 {len(PREP[Lu]['val_flows']):,} → 公共部分占 "
        f"{IN_COMMON[PREP[Lu]['val_flows']].mean():.4f}")

gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB pos_weight={_pos.item():.6f}")


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


@torch.no_grad()
def val_scores(net, gI, gM, gval, Lu):
    """返回 (预测, 标签, 流索引)，顺序对所有检查点一致。"""
    was_training = net.training
    net.eval(); P = []; Y = []; F = []
    for a in range(0, len(gval), 2048):
        sel = gval[a:a + 2048]; idx = gI[sel]; msk = gM[sel]; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, Lu, D), msk)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
        F.append(idx.reshape(-1)[fm].cpu().numpy())
    if was_training:
        net.train()
    return np.concatenate(P), np.concatenate(Y), np.concatenate(F)


def run_one(cfg, gI, gM, gtr, gval, Lu, n_epoch, spw):
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = Model(True, True, cfg["HID"]).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=LR)
    gen = torch.Generator().manual_seed(SEED)
    aux_w = cfg["AUX_W"]
    hist, snaps = [], []
    t0 = time.time(); net.train()
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
        P_, Y_, _F = val_scores(net, gI, gM, gval, Lu)
        hist.append([ep, float(average_precision_score(Y_, P_)), net.p.item()])
        snaps.append({k: t.detach().cpu().clone() for k, t in net.state_dict().items()})
        if ep % 10 == 0 or ep == n_epoch:
            log(f"    {cfg['name']} ep {ep:>2}/{n_epoch} 本L验证AP={hist[-1][1]:.6f} "
                f"累计{(time.time()-t0)/60:.1f}分")
    rank = sorted(range(n_epoch), key=lambda i: (-hist[i][1], hist[i][0]))
    top = sorted(rank[:TOPK])
    Pacc, Yv, Fv, ps = None, None, None, []
    for i in top:
        net.load_state_dict({k: v.to(dev) for k, v in snaps[i].items()})
        net.eval(); ps.append(net.p.item())
        P_, Y_, F_ = val_scores(net, gI, gM, gval, Lu)
        Pacc = P_ if Pacc is None else Pacc + P_
        Yv = Y_ if Yv is None else Yv
        Fv = F_ if Fv is None else Fv
    P_avg = Pacc / len(top)
    ap_own = float(average_precision_score(Yv, P_avg))
    m = IN_COMMON[Fv]
    ap_common = float(average_precision_score(Yv[m], P_avg[m]))
    log(f"  {cfg['name']} top5 epoch={[hist[i][0] for i in top]} | "
        f"本L验证AP={ap_own:.8f}（主运行 {cfg['val_ap_pred_avg']:.8f}，差 "
        f"{abs(ap_own-cfg['val_ap_pred_avg']):.3e}）| 公共流验证AP={ap_common:.8f} "
        f"（用了 {int(m.sum()):,} 条，正例率 {Yv[m].mean():.6f}）")
    return {"name": cfg["name"], "L": Lu, "AUX_W": aux_w, "HID": cfg["HID"],
            "topk_epochs": [hist[i][0] for i in top],
            "ap_own_val": ap_own, "ap_own_val_main_run": cfg["val_ap_pred_avg"],
            "repro_abs_diff": abs(ap_own - cfg["val_ap_pred_avg"]),
            "ap_common_val": ap_common, "n_common_used": int(m.sum()),
            "common_pos_rate": float(Yv[m].mean()), "p_pred_avg": float(np.mean(ps)),
            "train_seconds": time.time() - t0}


OUTR = {}
for Lu in (128, 64, 32):
    pr = PREP[Lu]
    gI = torch.from_numpy(pr["I"]).to(dev); gM = torch.from_numpy(pr["M"]).to(dev)
    gtr = torch.from_numpy(pr["tr"]).to(dev); gval = torch.from_numpy(pr["val"]).to(dev)
    log("-" * 100)
    log(f"L={Lu} 重训 {PICK[Lu]['name']}（{pr['n_epoch']} 轮）")
    OUTR[Lu] = run_one(PICK[Lu], gI, gM, gtr, gval, Lu, pr["n_epoch"], pr["spw"])
    del gI, gM, gtr, gval
    torch.cuda.empty_cache()

log("=" * 100)
_bad = [r["name"] for r in OUTR.values() if r["repro_abs_diff"] > 1e-9]
assert not _bad, f"以下配置未复现主运行的本L验证AP，本诊断作废：{_bad}"
log("复现校验通过：3 个配置的本 L 验证 AP 与主运行逐位一致（差 < 1e-9）")

own_rank = sorted(OUTR.values(), key=lambda r: -r["ap_own_val"])
com_rank = sorted(OUTR.values(), key=lambda r: -r["ap_common_val"])
log("既定协议口径（各 L 用各自验证流，正例率不同）排序：")
for i, r in enumerate(own_rank, 1):
    log(f"  {i}. L={r['L']:>3} {r['name']:<22} AP={r['ap_own_val']:.8f}")
log(f"公共验证流口径（{len(COMMON):,} 条，正例率 {y23[COMMON].mean():.6f}，完全可比）排序：")
for i, r in enumerate(com_rank, 1):
    log(f"  {i}. L={r['L']:>3} {r['name']:<22} AP={r['ap_common_val']:.8f}")
same = [r["L"] for r in own_rank] == [r["L"] for r in com_rank]
log("=" * 100)
log(f"★ 两种口径的 L 排序{'一致 → 跨 L 结论不是验证集口径漂移造成的' if same else '不一致 → 既定协议的跨 L 排序受验证集口径漂移影响，胜者的 L 不可直接采信'}")
log(f"  既定协议第一 L={own_rank[0]['L']}，公共流口径第一 L={com_rank[0]['L']}")

json.dump({"picked_per_L": {str(k): v for k, v in PICK.items()},
           "common_val_flows": int(len(COMMON)),
           "common_pos_rate": float(y23[COMMON].mean()),
           "per_L_val_pos_rate": {str(L): float(y23[PREP[L]["val_flows"]].mean()) for L in GRID_L},
           "results": {str(k): v for k, v in OUTR.items()},
           "rank_own_val": [r["name"] for r in own_rank],
           "rank_common_val": [r["name"] for r in com_rank],
           "rank_identical": bool(same),
           "caveat": "本诊断只统一了验证口径；训练集仍随 L 变化（同一时间尾部规则），该残余项未消除",
           "note": "纯验证侧诊断，不加载 LSPR24，不改变主运行已冻结的胜者"},
          open(f"{MAIN}/crossL_fair_val_diagnostic.json", "w"), ensure_ascii=False, indent=2)
log(f"已存 {MAIN}/crossL_fair_val_diagnostic.json 总耗时 {(time.time()-T0)/60:.1f} 分")
