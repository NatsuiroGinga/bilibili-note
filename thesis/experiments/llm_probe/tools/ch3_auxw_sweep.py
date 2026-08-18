# -*- coding: utf-8 -*-
"""第三章 CPA-ELP 训练配置扫描：辅助损失权重、辅助损失粒度、训练采样单元。

本脚本**只改训练配置，不改两个核心机制的数学形式，也不改评价口径**：
  机制一 因果前缀聚合  ctx_t = Σ_{i<=t} h_i / Σ_{i<=t} m_i   —— 逐字沿用 ch3_full.py:162-166
  机制二 实体级可学习 Lp 池化  S = (Σ s^p / n)^{1/p}, p = exp(p_log) —— 逐字沿用 ch3_full.py:150-152
  评价（实体键、实体聚合、DR@FPR 判据）—— 逐字沿用 ch3_full.py:130-133 / 213-225 / 227-240

要回答的问题：C11 的三处训练配置从未调过，它们能否把**实体级指标**推到冻结基准之上。
主指标是实体 AP(Lp) 与 DR@4%FPR（第三章决策单元是实体）；逐流 AP 一并报出但不作选择依据。

七个变体（同一进程内串行，共用一次数据加载）：
  A 组 辅助损失权重 AUX_W ∈ {0.25, 0.5, 1.0, 2.0, 4.0}，其中 1.0 即冻结基准 C11。
      动机：AUX_W 是逐流表现与实体表现之间的旋钮，从未调过。
      实测参照：C10（无辅助损失）逐流 AP 0.4278 / 实体 AP 0.3497；
                C11（AUX_W=1）逐流 AP 0.2316 / 实体 AP 0.4630。
  B 组 辅助损失改到实体级，AUX_W 取 A 组最优值。
      动机：Lp 池化训练时在**单条序列**内做，评价时在**整个实体**上做；
            实体超过 L=128 条流会被切成多条序列，两者不是同一个量。
      做法：一个 batch 内把属于同一实体的序列的逐流概率合并后再做一次 Lp 池化。
      batch 内同实体只有一条序列时精确退化为原做法（见 entity_aux 的 -1e30 掩码论证），
      这是预期行为，不是缺陷。
  C 组 训练采样单元改为「先均匀采实体、再从该实体的序列里采一条」，AUX_W 取 A 组最优值。
      动机：训练对序列均匀采样，评价却是每个实体一票，而实体的序列数差几百倍。

正确性锚点（硬断言，不复现即中止，不继续扫描）：
  基准配置 = AUX_W 1.0 + 序列级辅助 + 按序列均匀采样，其余全部照抄 C11，
  必须复现 runs/diagnostics/ch3-full/ch3_full_results.json 的 C11 一行。
  复现不了说明分块、检查点或实体聚合有一处退化，此时后面六个变体的数字不可比。

分块来源的选择：本脚本**直接消费冻结缓存 I23/M23/I24/M24**，而不是重新 lexsort 分块。
  ch3_full.py 的 C11 本身就是消费这份缓存产出的，直接复用是与冻结基准最强的对齐；
  ch3_e5e6.py 已实测「按实体 lexsort 后每 128 切一段」与该缓存逐元素相同，故两条路等价。
  B/C 两组需要的「序列 → 实体」映射由 ent23[I23[:,0]] 导出，并以逐元素断言校验
  （同一序列内所有未填充位置必须属于同一实体）。

不引入 SwanLab：这是调优扫描不是正式实验，且服务端近期返回 401。
"""

import json
import os
import time
import time as _t

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
OUT = f"{ROOT}/runs/diagnostics/ch3-auxw-sweep"
os.makedirs(OUT, exist_ok=True)

# ---- 以下超参数逐字取自 ch3_full.py，禁止在本脚本内调整 ----
L, BS, HID = 128, 64, 192
SEED = 42
STEPS = 20000
EPOCH_STEPS, AVG_LAST = 1000, 5
LR = 2e-3
EVAL_BS = 2048
MIN_FREE_GIB = 14.0

# ---- 冻结基准：runs/diagnostics/ch3-full/ch3_full_results.json 的 C11 一行 ----
ANCHOR = {
    "fap": 0.2315713900260571,
    "e_max": 0.3858276572759182,
    "e_lp": 0.46298806991944896,
    "dr": 0.6954787234042553,
    "p": 1.2235541820526123,
}
# 冻结 C11 的三种子逐流 AP 标准差（ch3_full.py E2 节），用于判断增量是否超噪声
C11_SEED_SD = 0.0586

# 选择规则在看到结果之前固定：A 组最优 = 实体 AP(Lp) 最大者，并列时看 DR@4%FPR。
# B/C 两组使用该 AUX_W。禁止看到结果后改判据。
SELECT_KEY, SELECT_TIEBREAK = "e_lp", "dr"

# =====================================================================
# 数据加载
# =====================================================================
dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "本脚本必须在 GPU 上运行"

_mi = torch.cuda.mem_get_info()
# 官方文档与 context7 抽取的片段对该元组顺序说法不一致（(free,total) vs (total,free)）。
# free <= total 恒成立，故用 min/max 取值，结果与顺序无关，不依赖任何一方的说法。
_free_gib, _total_gib = min(_mi) / 2**30, max(_mi) / 2**30
log(f"GPU 显存：空闲 {_free_gib:.2f} GiB / 总量 {_total_gib:.2f} GiB")
assert _free_gib >= MIN_FREE_GIB, (
    f"空闲显存 {_free_gib:.2f} GiB < 门槛 {MIN_FREE_GIB} GiB；"
    f"卡上另有实验在跑，本脚本必须让路，不得挤占"
)

y23 = np.load(f"{CACHE}/y23.npy")
y24 = np.load(f"{CACHE}/y24.npy")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")
I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
ent23 = np.load(f"{CACHE}/ent23.npy")
D = int(np.load(f"{CACHE}/X23.npy", mmap_mode="r").shape[1])
log(f"特征数 D={D} 训练流={len(y23):,} 评价流={len(y24):,} "
    f"训练序列={len(I23):,} 评价序列={len(I24):,}")

# 实体键：逐字沿用 ch3_full.py:130-133（2-IP 无向对）。20M 行的 Python 字符串拼接很慢，
# 结果只依赖冻结缓存 s24/d24，故首算后落盘到本脚本自己的产物目录，重跑直接复用。
ENT24_F = f"{OUT}/ent24_cache.npy"
if os.path.exists(ENT24_F):
    ent24 = np.load(ENT24_F)
    log("实体键缓存命中")
else:
    _t0 = _t.time()
    s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
    d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
    key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
    _, ent24 = np.unique(key24, return_inverse=True)
    ent24 = np.asarray(ent24).reshape(-1).astype(np.int64)
    np.save(ENT24_F, ent24)
    del s24, d24, key24
    log(f"实体键首次构建完成，用时 {_t.time()-_t0:.1f}s")
N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32)
np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 先验={ent_lab.mean():.10f}")

# 序列 → 实体映射。填充位指向流 0（rechunk 用 np.zeros 补位），故只校验未填充位置。
seq_ent = ent23[I23[:, 0]]
_ent_of_flow = ent23[I23]
_consistent = (_ent_of_flow == seq_ent[:, None]) | (M23 < 0.5)
assert _consistent.all(), (
    f"有 {int((~_consistent).sum())} 个未填充位置的实体与所在序列首元素不同，"
    f"说明缓存 I23 不是按实体分块的，B/C 两组的实体语义不成立"
)
del _ent_of_flow, _consistent
_order = np.argsort(seq_ent, kind="stable")
_sorted_ent = seq_ent[_order]
_starts = np.flatnonzero(np.r_[True, _sorted_ent[1:] != _sorted_ent[:-1]])
_counts = np.diff(np.r_[_starts, len(_order)])
N_ENT_TR = len(_starts)
log(f"LSPR23 有序列的实体={N_ENT_TR:,}  每实体序列数 中位={np.median(_counts):.0f} "
    f"均值={_counts.mean():.3f} 最大={_counts.max():,}  "
    f"头部 0.1% 实体占序列比例={np.sort(_counts)[::-1][:max(1,N_ENT_TR//1000)].sum()/len(I23):.4f}")
t_order = torch.from_numpy(_order.astype(np.int64))
t_starts = torch.from_numpy(_starts.astype(np.int64))
t_counts = torch.from_numpy(_counts.astype(np.int64))


def to_gpu_matrix(name):
    """分块上卡，避免 5~6 GiB 的宿主机整块副本。"""
    a = np.load(f"{CACHE}/{name}.npy", mmap_mode="r")
    g = torch.empty(tuple(a.shape), dtype=torch.float32, device=dev)
    step = 2_000_000
    for i in range(0, a.shape[0], step):
        g[i:i + step] = torch.from_numpy(np.ascontiguousarray(a[i:i + step])).to(dev)
    del a
    return g


gX23 = to_gpu_matrix("X23")
gX24 = to_gpu_matrix("X24")
gy23 = torch.from_numpy(y23).to(dev)
gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
g_seq_ent = torch.from_numpy(seq_ent.astype(np.int64)).to(dev)
log(f"矩阵已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB "
    f"（剩余空闲 {min(torch.cuda.mem_get_info())/2**30:.2f} GiB）")


# =====================================================================
# 模型与损失：逐字沿用 ch3_full.py:150-172 的 C11 分支（agg=True, lp=True）
# =====================================================================
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


class Model(nn.Module):
    """参数创建顺序与 ch3_full.py 完全一致，否则同一 seed 下初始化的随机数流会错位。"""

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
log(f"序列级正类率={_sl.mean():.6f} 序列级损失权重 spw={_spw:.4f} 逐流 pos_weight={float(_pos):.4f}")
# C 组只改采样单元这一个变量，故 spw 与逐流 pos_weight 沿用全量序列集合上的取值，不随采样重算。


def entity_aux(lo, msk, ysq, sel, p_):
    """B 组：batch 内按实体合并序列后再做一次 Lp 池化。

    S_e = (Σ_{f ∈ 该实体在本 batch 的全部流} s_f^p / n_e)^{1/p}，与评价端算子同形。
    非成员位置填 -1e30 后 logsumexp：exp(-1e30 - max) 在 float32 下恒为 0，
    故某实体在 batch 内只有一条序列时，本函数与 lp_pool 的取值精确相同（退化为原做法）。
    """
    eb = g_seq_ent[sel]
    uq, inv = torch.unique(eb, return_inverse=True)
    G = int(uq.numel())
    mem = inv.unsqueeze(0) == torch.arange(G, device=lo.device).unsqueeze(1)   # (G, BS)
    memf = mem.to(lo.dtype)
    ls = torch.log(torch.sigmoid(lo).clamp(min=1e-7))
    lse_seq = torch.logsumexp((p_ * ls).masked_fill(msk < 0.5, -1e30), 1)      # (BS,)
    n_seq = msk.sum(1)                                                        # (BS,)
    # 先 expand 到 (G, BS) 再 masked_fill：self 与 mask 形状完全一致，
    # 不依赖 masked_fill 是否会把 self 一并广播（该行为在文档里没有明确承诺）。
    lse_g = torch.logsumexp(lse_seq.unsqueeze(0).expand(G, -1).masked_fill(~mem, -1e30), 1)  # (G,)
    n_g = (n_seq.unsqueeze(0) * memf).sum(1).clamp(min=1.0)
    s_g = torch.exp((lse_g - torch.log(n_g)) / p_).clamp(1e-6, 1 - 1e-6)
    y_g = (ysq.unsqueeze(0) * memf).amax(1)
    return s_g, y_g, G


def train_one(name, aux_w, aux_level="seq", sampler="seq", seed=SEED):
    """aux_level ∈ {seq, entity}；sampler ∈ {seq, entity}。其余一切照抄 C11。"""
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(True, True, HID).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW(
        [{"params": dec, "weight_decay": 0.01}, {"params": nod, "weight_decay": 0.0}], lr=LR)
    gen = torch.Generator().manual_seed(seed)
    snaps = []; t0 = _t.time(); hb = max(1, STEPS // 20)
    g_sum, g_min = 0, BS
    net.train()
    for st in range(STEPS):
        if sampler == "seq":
            sel = torch.randint(0, len(I23), (BS,), generator=gen).to(dev)
        else:
            e = torch.randint(0, N_ENT_TR, (BS,), generator=gen)
            u = torch.rand(BS, generator=gen, dtype=torch.float64)
            off = torch.minimum((u * t_counts[e].to(torch.float64)).to(torch.int64),
                                t_counts[e] - 1)
            sel = t_order[t_starts[e] + off].to(dev)
        idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]
        xb = gX23[idx.reshape(-1)].reshape(BS, L, D); yb = gy23[idx.reshape(-1)].reshape(BS, L)
        lo = net(xb, msk)
        loss = (_lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
        ysq = (yb * msk).amax(1)
        if aux_level == "seq":
            sq = lp_pool(torch.sigmoid(lo), msk, net.p).clamp(1e-6, 1 - 1e-6)
            yq = ysq
        else:
            sq, yq, G = entity_aux(lo, msk, ysq, sel, net.p)
            g_sum += G; g_min = min(g_min, G)
        w = 1.0 + (_spw - 1.0) * yq
        loss = loss + aux_w * ((_bs(sq, yq) * w).sum() / w.sum())
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        if (st + 1) % hb == 0:
            el = _t.time() - t0
            log(f"    {name} 步 {st+1:,}/{STEPS:,} loss={float(loss.detach()):.5f} "
                f"p={float(net.p.detach()):.4f} {(st+1)/max(el,1e-9):.1f}步/秒 "
                f"已用{el/60:.1f}分 预计剩余{(STEPS-st-1)/max((st+1)/max(el,1e-9),1e-9)/60:.1f}分")
        # 检查点判据逐字沿用 ch3_full.py:192-193 → 第 16000/17000/18000/19000/20000 步
        if STEPS - st <= AVG_LAST * EPOCH_STEPS and (st + 1) % EPOCH_STEPS == 0:
            snaps.append({k: v.detach().clone() for k, v in net.state_dict().items()})
    tr_t = _t.time() - t0
    assert len(snaps) == AVG_LAST, f"{name} 检查点数 {len(snaps)} != {AVG_LAST}"

    acc = None; seen = None; ps = []; t1 = _t.time()
    for sd_ in snaps:
        net.load_state_dict(sd_); net.eval(); ps.append(net.p.item())
        sc = torch.zeros(len(y24), device=dev)
        sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
        with torch.no_grad():
            for a in range(0, len(I24), EVAL_BS):
                idx = gI24[a:a + EVAL_BS][:, :L]; msk = gM24[a:a + EVAL_BS][:, :L]; b = idx.shape[0]
                pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
                fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
                sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
        s_ = sc.cpu().numpy(); n_ = sn.cpu().numpy()
        acc = s_ if acc is None else acc + s_
        seen = n_ if seen is None else (seen | n_)
    ev_t = _t.time() - t1
    del snaps
    torch.cuda.empty_cache()
    extra = {}
    if aux_level == "entity":
        extra = {"mean_groups_per_batch": g_sum / STEPS, "min_groups_per_batch": g_min,
                 "mean_merged_seqs_per_batch": BS - g_sum / STEPS}
    return acc / AVG_LAST, seen, float(np.mean(ps)), tr_t, ev_t, extra


# =====================================================================
# 评价：逐字沿用 ch3_full.py:213-240（去掉本实验用不到的 first_k 分支）
# =====================================================================
def _ent_scores(sc, seen, p):
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[seen], sc[seen])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[seen], np.clip(sc[seen], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[seen], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    return es


def ent_ap(sc, seen, p=None):
    es = _ent_scores(sc, seen, p); ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), int(ok.sum())


def dr_at_fpr(sc, seen, target=0.04, p=None):
    es = _ent_scores(sc, seen, p); ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0: return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


def evaluate(name, cfg, sc, seen, p, tr_t, ev_t, extra):
    fap = average_precision_score(y24[seen], sc[seen])
    fauc = roc_auc_score(y24[seen], sc[seen])
    e_max, n_ent = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, p)
    dr = dr_at_fpr(sc, seen, 0.04, p)
    r = dict(cfg); r.update(name=name, fap=float(fap), fauc=float(fauc), e_max=float(e_max),
                            e_lp=float(e_lp), dr=float(dr), p=float(p), n_ent=n_ent,
                            coverage=float(seen.mean()), train_sec=float(tr_t),
                            eval_sec=float(ev_t), **extra)
    log(f"  ▸ {name}: 逐流AP={fap:.6f} AUC={fauc:.6f} 实体AP(max)={e_max:.6f} "
        f"实体AP(Lp)={e_lp:.6f} DR@4%FPR={dr:.4f} p={p:.4f} "
        f"训练{tr_t/60:.1f}分 推理{ev_t:.0f}秒 覆盖={seen.mean():.6f}")
    return r


RES = []
RES_F = f"{OUT}/auxw_sweep_results.json"


def dump():
    json.dump({"anchor_C11": ANCHOR, "c11_seed_sd_flow_ap": C11_SEED_SD,
               "select_rule": {"primary": SELECT_KEY, "tiebreak": SELECT_TIEBREAK,
                               "note": "在看到任何结果之前固定"},
               "protocol": {"L": L, "BS": BS, "HID": HID, "seed": SEED, "steps": STEPS,
                            "lr": LR, "avg_last": AVG_LAST, "epoch_steps": EPOCH_STEPS,
                            "spw": _spw, "flow_pos_weight": float(_pos)},
               "variants": RES},
              open(RES_F, "w"), ensure_ascii=False, indent=2)


def run(name, aux_w, aux_level="seq", sampler="seq"):
    cfg = {"aux_w": aux_w, "aux_level": aux_level, "sampler": sampler}
    log(f"── 开始 {name}  {cfg}")
    sc, seen, p, tr_t, ev_t, extra = train_one(name, aux_w, aux_level, sampler)
    r = evaluate(name, cfg, sc, seen, p, tr_t, ev_t, extra)
    RES.append(r); dump()
    return r


log("=" * 96)
log("第 0 步：复现冻结基准 C11（AUX_W=1.0 + 序列级辅助 + 按序列均匀采样）")
base = run("A-序列级辅助-权重1.00（冻结基准C11）", 1.0)
d_fap = abs(base["fap"] - ANCHOR["fap"])
d_elp = abs(base["e_lp"] - ANCHOR["e_lp"])
d_p = abs(base["p"] - ANCHOR["p"])
d_emax = abs(base["e_max"] - ANCHOR["e_max"])
d_dr = abs(base["dr"] - ANCHOR["dr"])
log(f"  锚点校验：逐流AP Δ={d_fap:.3e}  实体AP(Lp) Δ={d_elp:.3e}  p Δ={d_p:.3e}  "
    f"实体AP(max) Δ={d_emax:.3e}  DR Δ={d_dr:.3e}")
RES[-1]["anchor_delta"] = {"fap": d_fap, "e_lp": d_elp, "p": d_p, "e_max": d_emax, "dr": d_dr}
dump()
assert d_fap < 1e-3 and d_elp < 1e-3 and d_p < 1e-2, (
    f"基准配置未复现冻结 C11（Δ逐流AP={d_fap:.3e} Δ实体AP(Lp)={d_elp:.3e} Δp={d_p:.3e}）；"
    f"训练流、检查点或实体聚合存在退化，后续六个变体的数字不可比，就地中止"
)
log("  基准复现通过，继续扫描")

log("=" * 96)
log("A 组：辅助损失权重扫描")
for w in (0.25, 0.5, 2.0, 4.0):
    run(f"A-序列级辅助-权重{w:.2f}", w)

group_a = [r for r in RES if r["aux_level"] == "seq" and r["sampler"] == "seq"]
best = max(group_a, key=lambda r: (r[SELECT_KEY], r[SELECT_TIEBREAK]))
BEST_W = best["aux_w"]
log(f"A 组最优（按预先固定的 {SELECT_KEY}，并列看 {SELECT_TIEBREAK}）："
    f"{best['name']}  AUX_W={BEST_W}  实体AP(Lp)={best['e_lp']:.6f}  DR={best['dr']:.4f}")

log("=" * 96)
log(f"B 组：辅助损失改到实体级（AUX_W={BEST_W}，取自 A 组最优）")
run(f"B-实体级辅助-权重{BEST_W:.2f}", BEST_W, aux_level="entity")

log("=" * 96)
log(f"C 组：按实体采样（AUX_W={BEST_W}，取自 A 组最优）")
run(f"C-按实体采样-序列级辅助-权重{BEST_W:.2f}", BEST_W, sampler="entity")

log("=" * 96)
log("全部变体完成，对照表（主指标：实体 AP(Lp) 与 DR@4%FPR）")
hdr = f"{'变体':<34}{'逐流AP':>11}{'实体AP(max)':>13}{'实体AP(Lp)':>13}{'DR@4%FPR':>11}{'p':>9}{'训练分':>9}"
print(hdr, flush=True)
for r in RES:
    print(f"{r['name']:<34}{r['fap']:>11.6f}{r['e_max']:>13.6f}{r['e_lp']:>13.6f}"
          f"{r['dr']:>11.4f}{r['p']:>9.4f}{r['train_sec']/60:>9.1f}", flush=True)
print(f"{'冻结基准 C11（ch3_full.py）':<34}{ANCHOR['fap']:>11.6f}{ANCHOR['e_max']:>13.6f}"
      f"{ANCHOR['e_lp']:>13.6f}{ANCHOR['dr']:>11.4f}{ANCHOR['p']:>9.4f}{'--':>9}", flush=True)

log("-" * 96)
log("相对冻结基准的增量（主指标）")
for r in RES:
    log(f"  {r['name']:<34} Δ实体AP(Lp)={r['e_lp']-ANCHOR['e_lp']:+.6f}  "
        f"ΔDR@4%FPR={r['dr']-ANCHOR['dr']:+.4f}  Δ逐流AP={r['fap']-ANCHOR['fap']:+.6f}")
win = [r for r in RES if r["e_lp"] > ANCHOR["e_lp"] and r["dr"] > ANCHOR["dr"]]
if win:
    b = max(win, key=lambda r: r["e_lp"])
    log(f"两项主指标同时超过冻结基准的变体共 {len(win)} 个，最优为 {b['name']}："
        f"实体AP(Lp) {b['e_lp']:.6f}（{b['e_lp']-ANCHOR['e_lp']:+.6f}）"
        f" DR {b['dr']:.4f}（{b['dr']-ANCHOR['dr']:+.4f}）")
else:
    log("没有任何变体在两项主指标上同时超过冻结基准。如实报告「未发现提升」，不换指标、不调判据。")
log(f"单种子结论的噪声参照：冻结 C11 的三种子逐流 AP 标准差 = {C11_SEED_SD}。"
    f"任何小于该量级的增量都必须按单种子噪声处理，需多种子复核后才能进正文。")
dump()
log(f"结果已存 {RES_F}")
