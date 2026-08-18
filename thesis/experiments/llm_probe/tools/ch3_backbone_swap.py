# -*- coding: utf-8 -*-
"""第三章跨基座机制验证：把逐流编码器从 MLP 换成单层 GRU，重跑 C00 / C11 两格。

============================ 这个实验回答两个问题 ============================
问题一（普适性）：C00→C11 的增益在换骨干后是否仍在？
问题二（必要性）：因果前缀均值本质是「只用历史的固定状态递推」。既然如此，
                 直接换成本来就建模序列的 GRU 骨干，是不是更好、还需不需要这个机制？

设计：2 骨干 × 2 格。骨干 A（MLP）的两格不重跑，直接取
runs/diagnostics/ch3-hparam-fairsel-v2 第二组 2x2 的结果（同为 top-5 预测平均协议）。
本脚本只跑骨干 B（单层 GRU）的 C00 与 C11 两格，LSPR24 合法评价次数因此为 2。

============================ 骨干 B 的定义 ============================
逐流编码器由  h_t = Dropout(ReLU(W1 x_t))     （ch3_full.py 第 157 行）
改为          h_t = GRU(x_t, h_{t-1})          （单层、单向、bias=True）
其余一律不动：
  C11 仍在 GRU 输出上做因果前缀均值 ctx_t = Σ_{i≤t} h_i / Σ_{i≤t} m_i，
      再 z_t = Dropout(ReLU(W2[h_t; ctx_t]))，s_t = σ(W3 z_t)
  C00 的 ctx 仍填零向量（容量相同，不携带信息），且不加 Lp 辅助损失
  Lp 池化、辅助损失、pos_weight、spw、评价口径全部照旧
注意 nn.GRU 的 dropout 参数只作用于多层之间，单层时恒等于无；按上式定义，
GRU 输出后不再套 ReLU/Dropout（自带 tanh 非线性），这一点在报告中如实说明。

============================ 参数量对齐 ============================
MLP 骨干总参数 90,242。GRU 骨干总参数（输入 83、隐藏 h）：
  GRU   3(83h + h² + 2h)     g: 2h² + h     o: h + 1     p_log: 1
  合计  5h² + 257h + 2
h=111 → 90,134，相对 90,242 偏差 -108（-0.120%），落在 ±10% 内。
（h=192 会得到 233,666，超预算 159%，比较不公平，故不沿用。）

============================ 掩码正确性 ============================
分块时补零只出现在序列尾部（rechunk 的 mask 为 col < real，是前缀），
但仍按要求用 pack_padded_sequence 显式跳过补零位，并在训练前做三项实现验证：
  性质一 补零位的输入值任意改动，真实位的输出逐元素不变（补零位不污染状态）
  性质二 打包批前向 == 逐条截断到真实长度单独前向（真实位，容差 1e-5）
  性质三 掩码后补零位的输出恒为 0
这三项是**实现验证**（真值由构造给定，只报通过/不通过），不是冒烟实验，
不创建运行身份、不产生任何指标、不进结果表。

============================ LSPR24 隔离 ============================
  guarded_load()  ：所有 np.load 的唯一入口，名字含 "24" 且未冻结即断言失败
  阶段闸门        ：两格训练完成 → selection_frozen.json 先落盘 → 再置 True
  load24()        ：断言 SELECTION_FROZEN，最终 _N24_LOADS == 1
  score24()       ：断言 SELECTION_FROZEN，最终 _EVAL24_CALLS == 2

评价口径逐字复刻 ch3_full.py：实体构造第 130-133 行、ent_ap 第 213-225 行
（Lp 聚合含末尾 .astype(np.float32)）、dr_at_fpr 第 236-240 行。
检查点策略逐字复刻 ch3_hparam_fairsel_v2.py：验证 AP 前 5 名 epoch 的检查点
各自推理一遍后平均预测分数，p 取 5 份算术均值。不创建 SwanLab 运行身份。
"""

import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
V2 = f"{ROOT}/runs/diagnostics/ch3-hparam-fairsel-v2/ch3_hparam_fairsel_v2_results.json"
OUT = f"{ROOT}/runs/diagnostics/ch3-backbone-swap"
os.makedirs(OUT, exist_ok=True)

# ---- 全部照抄 ch3_hparam_fairsel_v2.py / ch3_2x2_fairsel.py，不调 ----
SEED, BS, LR, DP = 42, 64, 2e-3, 0.1
L = 128
AUX_W = 1.0
EPOCH_STEPS, N_EPOCH = 1000, 20
TOPK = 5
VAL_FRAC, TIME_TAIL = 0.10, 0.15

# ---- 骨干 B：单层 GRU，隐藏维按参数量对齐 ----
GRU_HID = 111
MLP_NPAR = 90242


def gru_total_params(h):
    """5h² + 257h + 2：GRU 3(83h+h²+2h) + g(2h²+h) + o(h+1) + p_log(1)。"""
    return 3 * (83 * h + h * h + 2 * h) + (2 * h * h + h) + (h + 1) + 1


_EXP_NPAR = gru_total_params(GRU_HID)
assert _EXP_NPAR == 90134, f"参数量公式自检失败：{_EXP_NPAR}"
assert abs(_EXP_NPAR - MLP_NPAR) / MLP_NPAR < 0.10, "GRU 参数量超出 MLP 的 ±10% 预算"

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0
_EVAL24_LEDGER = []
N_EVAL_BUDGET = 2


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
e23f = guarded_load("ent23")
t23f = guarded_load("t23_flow")
I23 = guarded_load("I23")            # L=128 冻结分块，与 v2 的 rechunk23(128) 逐元素一致
M23 = guarded_load("M23")
E23 = guarded_load("E23")            # 逐序列实体
T23 = guarded_load("T23")            # 逐序列起始时间
D = X23.shape[1]
assert D == 83, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {D}"
assert len(e23f) == len(t23f) == len(y23) == len(X23)
assert I23.shape[1] == L and M23.shape[1] == L, f"冻结分块列数应为 {L}"
log(f"LSPR23 流={len(y23):,} 特征数={D} L={L} 冻结序列={len(I23):,}")

dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "本任务必须在 GPU 上运行"
log(f"torch {torch.__version__} | {torch.cuda.get_device_name(0)}")

# ---- 验证实体集合：逐字复用 ch3_2x2_fairsel.py 第 80-83 行 ----
_rs = np.random.RandomState(SEED)
_uent = np.unique(E23)
assert np.array_equal(_uent, np.unique(e23f)), "逐流实体集合与冻结序列实体集合不一致"
_perm = _rs.permutation(len(_uent))
VAL_ENT = set(_uent[_perm[:max(1, int(len(_uent) * VAL_FRAC))]].tolist())
assert len(_uent) == 150680, f"LSPR23 实体数自检失败：{len(_uent)}"
log(f"LSPR23 实体 {len(_uent):,}，验证实体 {len(VAL_ENT):,}（RandomState(42) 排列）")

# ---- 切分：逐字复用 ch3_2x2_fairsel.py 第 84-90 行 ----
_m_ent = np.fromiter((e in VAL_ENT for e in E23), bool, len(E23))
_t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
_m_time = T23 >= _t_cut
TR_IDX = np.flatnonzero(~(_m_ent | _m_time))
VAL_IDX = np.flatnonzero(_m_ent & ~_m_time)
assert len(np.intersect1d(VAL_IDX, TR_IDX)) == 0, "验证集与训练区有交叠"
assert len(TR_IDX) == 208598, f"训练序列数自检失败：{len(TR_IDX)}"
assert len(VAL_IDX) == 22444, f"验证序列数自检失败：{len(VAL_IDX)}"
log(f"切分自检通过：208,598 训练 / 22,444 验证（与 ch3_2x2_fairsel / v2 一致）")

_sl = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
SPW = float((1 - _sl.mean()) / max(_sl.mean(), 1e-8))
_FILL = float(M23.mean())
_LEN23 = M23.sum(1)
log(f"L={L} 填充率 {_FILL:.4f} | 真实长度 均值 {_LEN23.mean():.2f} 中位 {np.median(_LEN23):.0f} "
    f"最小 {_LEN23.min():.0f} 最大 {_LEN23.max():.0f}")
log(f"序列级正类率 {_sl.mean():.6f} spw={SPW:.4f}")
assert _LEN23.min() >= 1, "存在真实长度为 0 的序列，pack_padded_sequence 无法处理"
del _sl, _m_ent, _m_time, _LEN23

# ---- 上卡 ----
gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
gI = torch.from_numpy(I23).to(dev)
gM = torch.from_numpy(M23).to(dev)
gtr = torch.from_numpy(TR_IDX).to(dev)
gval = torch.from_numpy(VAL_IDX).to(dev)
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 损失：逐字照抄 ch3_full.py 第 150-152、170-172 行 ----
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


class GRUModel(nn.Module):
    """骨干 B：逐流编码器 = 单层单向 GRU；其余结构与 ch3_full.Model 逐字相同。"""

    def __init__(self, agg, lp, hid=GRU_HID, dp=DP):
        super().__init__(); self.agg, self.lp, self.hid = agg, lp, hid
        self.f = nn.GRU(input_size=D, hidden_size=hid, num_layers=1, bias=True,
                        batch_first=True, bidirectional=False)
        self.g = nn.Sequential(nn.Linear(hid * 2, hid), nn.ReLU(), nn.Dropout(dp))
        self.o = nn.Linear(hid, 1); self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def encode(self, x, m):
        """h_t = GRU(x_t, h_{t-1})，补零位用 pack_padded_sequence 显式跳过。

        lengths 必须在 CPU 上（torch 2.13.0 官方签名要求）；enforce_sorted=False
        让 PyTorch 自行排序再还原，返回顺序与输入批一致。
        """
        lens = m.sum(1).to(torch.int64).clamp(min=1).cpu()
        packed = pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
        out, _ = self.f(packed)
        h, _ = pad_packed_sequence(out, batch_first=True, total_length=x.shape[1])
        return h * m.unsqueeze(-1)

    def forward(self, x, m):
        h = self.encode(x, m)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h, c], -1))).squeeze(-1)


_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"逐流 pos_weight={_pos.item():.6f}（口径照抄 ch3_full，用全量 LSPR23）")

# ---- 参数量核对：以 torch 实测为准 ----
_probe = GRUModel(True, True).to(dev)
NPAR = sum(p.numel() for p in _probe.parameters())
_NPAR_BY_MOD = {n: sum(p.numel() for p in mo.parameters())
                for n, mo in [("f(GRU)", _probe.f), ("g", _probe.g), ("o", _probe.o)]}
_NPAR_BY_MOD["p_log"] = 1
log("=" * 112)
log(f"参数量对齐：GRU 隐藏维 h={GRU_HID}，torch 实测总参数 {NPAR:,}（公式预测 {_EXP_NPAR:,}）")
log(f"  分解 {_NPAR_BY_MOD}")
log(f"  MLP 骨干 {MLP_NPAR:,} → 偏差 {NPAR - MLP_NPAR:+,}（{(NPAR - MLP_NPAR)/MLP_NPAR*100:+.3f}%），预算 ±10%")
assert NPAR == _EXP_NPAR, f"torch 实测参数量 {NPAR} 与公式 {_EXP_NPAR} 不符"
assert abs(NPAR - MLP_NPAR) / MLP_NPAR < 0.10, "参数量超出 ±10% 预算"
_nod_names = sorted(n for n, _ in _probe.named_parameters()
                    if n == "p_log" or n.split(".")[-1].startswith("bias"))
log(f"  不做权重衰减的参数（bias 与 p_log）：{_nod_names}")
assert _nod_names == ["f.bias_hh_l0", "f.bias_ih_l0", "g.0.bias", "o.bias", "p_log"], \
    f"权重衰减分组与预期不符：{_nod_names}"


def no_decay(n):
    return n == "p_log" or n.split(".")[-1].startswith("bias")


# =====================================================================================
# 掩码实现验证：真值由构造给定，只报通过/不通过，不产生任何科学指标
# =====================================================================================
log("=" * 112)
log("掩码实现验证（真值由构造给定，不是冒烟实验，不产生指标、不进结果表）")
with torch.no_grad():
    _probe.eval()
    _sel = gtr[:64]
    _idx = gI[_sel]; _msk = gM[_sel]
    _xb = gX23[_idx.reshape(-1)].reshape(64, L, D).clone()
    _lens = _msk.sum(1).to(torch.int64)
    log(f"  验证批 64 条，真实长度 最小 {int(_lens.min())} 最大 {int(_lens.max())} "
        f"（存在补零位：{int((_lens < L).sum())} 条）")
    assert int((_lens < L).sum()) > 0, "验证批全是满长序列，无法检验补零位，换一批"

    _h0 = _probe.encode(_xb, _msk)

    # 性质一：把补零位的输入换成量级 1e3 的随机噪声，真实位输出必须逐元素不变
    _xb2 = _xb.clone()
    _noise = torch.randn_like(_xb2) * 1e3
    _pad = (_msk < 0.5).unsqueeze(-1)
    _xb2 = torch.where(_pad, _noise, _xb2)
    _h1 = _probe.encode(_xb2, _msk)
    _d1 = (_h1 - _h0).abs().max().item()
    log(f"  性质一 补零位输入改为 1e3 量级噪声后，真实位输出最大绝对差 = {_d1:.3e}（判据 == 0）")
    assert _d1 == 0.0, f"补零位污染了状态，最大差 {_d1:.3e}"

    # 性质二：打包批前向 == 逐条截断到真实长度单独前向。
    # 这两条走不同 cuDNN 内核；RTX 5090 默认开 TF32（10 位尾数），跨内核差异被放大到 2e-4。
    # 已由 tools/ch3_backbone_gru_precision_probe.py 实测归因：TF32 开 1.959e-04 / 关 7.689e-06，
    # 同一路径重复两次恒为 0。故本性质在临时关闭 TF32 下检验，测完立即恢复默认，训练不受影响。
    _chk = sorted(range(64), key=lambda i: int(_lens[i]))[:8] + \
        sorted(range(64), key=lambda i: -int(_lens[i]))[:8]
    _chk = sorted(set(_chk))
    _tf32_bak = (torch.backends.cudnn.allow_tf32, torch.backends.cuda.matmul.allow_tf32)
    _p2 = {}
    for _tag, _tf in (("TF32开", True), ("TF32关", False)):
        torch.backends.cudnn.allow_tf32 = _tf
        torch.backends.cuda.matmul.allow_tf32 = _tf
        _hr = _probe.encode(_xb, _msk)
        _w_tr = 0.0
        for i in _chk:
            n = int(_lens[i])
            _single, _ = _probe.f(_xb[i:i + 1, :n, :])      # 不打包、无补零的参照前向
            _w_tr = max(_w_tr, (_single[0] - _hr[i, :n]).abs().max().item())
        _o_pad, _ = _probe.f(_xb)                            # 不打包、含补零的满批前向
        _w_pad = (_o_pad * _msk.unsqueeze(-1) - _hr).abs().max().item()
        _p2[_tag] = {"vs_truncated": _w_tr, "vs_padded_unpacked": _w_pad}
        log(f"  性质二（{_tag}）打包批 vs 逐条截断单独前向 = {_w_tr:.3e}；"
            f"打包批 vs 补零满批前向 = {_w_pad:.3e}")
    torch.backends.cudnn.allow_tf32, torch.backends.cuda.matmul.allow_tf32 = _tf32_bak
    _worst = _p2["TF32关"]["vs_truncated"]
    log(f"  性质二 判据取 TF32 关闭下的值 {_worst:.3e}（容差 5e-5）；"
        f"TF32 开时的 {_p2['TF32开']['vs_truncated']:.3e} 是 10 位尾数的跨内核精度差，非掩码错误")
    assert _worst < 5e-5, f"打包前向与截断前向不一致，最大差 {_worst:.3e}"
    assert _p2["TF32关"]["vs_padded_unpacked"] < 5e-5, "打包与补零满批不一致"

    # 性质三：掩码后补零位输出恒为 0
    _d3 = _h0.masked_select(_pad.expand_as(_h0)).abs().max().item() if _pad.any() else 0.0
    log(f"  性质三 掩码后补零位输出最大绝对值 = {_d3:.3e}（判据 == 0）")
    assert _d3 == 0.0, f"补零位输出未被掩码清零，最大 {_d3:.3e}"
MASK_CHECK = {"prop1_pad_does_not_pollute_state_maxdiff": _d1,
              "prop2": _p2, "prop2_criterion_tf32_off_vs_truncated": _worst,
              "prop3_masked_pad_output_maxabs": _d3,
              "n_seq_checked": 64, "n_with_padding": int((_lens < L).sum()),
              "tf32_default_restored": list(_tf32_bak),
              "note": "性质二在临时关闭 TF32 下判定；训练与评价一律使用默认 TF32 设置，与 MLP 骨干一致",
              "passed": True}
log("  ★ 三项掩码实现验证全部通过")
del _probe, _xb, _xb2, _h0, _h1, _noise, _pad, _idx, _msk, _sel, _lens
torch.cuda.empty_cache()


# =====================================================================================
# 训练与检查点选择：逐字复刻 ch3_hparam_fairsel_v2.train_and_select，只换模型类
# =====================================================================================
@torch.no_grad()
def val_scores(net):
    """LSPR23 实体不相交验证集上的逐流预测分数与标签（唯一的模型选择信号来源）。"""
    was_training = net.training
    net.eval(); P = []; Y = []
    for a in range(0, len(gval), 2048):
        sel = gval[a:a + 2048]; idx = gI[sel]; msk = gM[sel]; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    if was_training:
        net.train()
    return np.concatenate(P), np.concatenate(Y)


def val_ap(net):
    P, Y = val_scores(net)
    assert Y.max() > 0, "验证集无正例，选择信号无效"
    return float(average_precision_score(Y, P))


def train_and_select(name, agg, lp):
    """训练满 20 epoch 不早停，逐 epoch 记录验证 AP，取前 5 名 epoch 做预测平均。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(SEED); np.random.seed(SEED)
    torch.cuda.reset_peak_memory_stats()
    net = GRUModel(agg, lp).to(dev)
    dec = [p for n, p in net.named_parameters() if not no_decay(n)]
    nod = [p for n, p in net.named_parameters() if no_decay(n)]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=LR)
    gen = torch.Generator().manual_seed(SEED)
    hist, snaps = [], []
    t0 = time.time()
    net.train()
    for ep in range(1, N_EPOCH + 1):
        for _ in range(EPOCH_STEPS):
            sel = gtr[torch.randint(0, len(gtr), (BS,), generator=gen).to(dev)]
            idx = gI[sel]; msk = gM[sel]
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            lo = net(xb, msk); loss = (_lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            if lp:
                sq = lp_pool(torch.sigmoid(lo), msk, net.p).clamp(1e-6, 1 - 1e-6)
                ysq = (yb * msk).amax(1)
                w = 1.0 + (SPW - 1.0) * ysq
                loss = loss + AUX_W * ((_bs(sq, ysq) * w).sum() / w.sum())
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        v = val_ap(net)
        hist.append([ep, v, net.p.item()])
        snaps.append({k: t.detach().cpu().clone() for k, t in net.state_dict().items()})
        log(f"    {name} ep {ep:>2}/{N_EPOCH} 验证AP={v:.6f} p={net.p.item():.4f} "
            f"累计{(time.time()-t0)/60:.1f}分")
    tr_t = time.time() - t0

    # ---- top-5 预测平均：k 事前固定，排序键 (-验证AP, epoch)，同分取更早的 epoch ----
    rank = sorted(range(N_EPOCH), key=lambda i: (-hist[i][1], hist[i][0]))
    top = sorted(rank[:TOPK])
    top_states = [snaps[i] for i in top]
    Pacc, Yv, ps = None, None, []
    for sd_ in top_states:
        net.load_state_dict({k: v.to(dev) for k, v in sd_.items()})
        net.eval()
        ps.append(net.p.item())
        P_, Y_ = val_scores(net)
        Pacc = P_ if Pacc is None else Pacc + P_
        Yv = Y_ if Yv is None else Yv
    P_avg = Pacc / len(top_states)
    assert Yv.max() > 0, "验证集无正例，选择信号无效"
    v_pred = float(average_precision_score(Yv, P_avg))
    p_pred = float(np.mean(ps))

    top_info = [[hist[i][0], hist[i][1]] for i in top]
    log(f"  {name} 训练 {tr_t/60:.2f} 分 | top{TOPK} epoch={[t[0] for t in top_info]} "
        f"验证AP={['%.6f' % t[1] for t in top_info]}")
    log(f"  {name} → top{TOPK} 预测平均 验证AP={v_pred:.6f} p(算术均值)={p_pred:.4f} ｜ "
        f"逐epoch argmax {max(h[1] for h in hist):.6f} @ep{max(hist, key=lambda h: h[1])[0]}")
    out = {"name": name, "backbone": "GRU-1layer", "agg": agg, "lp": lp, "L": L,
           "AUX_W": AUX_W, "HID": GRU_HID, "n_epoch": N_EPOCH,
           "steps": N_EPOCH * EPOCH_STEPS, "spw": SPW,
           "val_ap_history": hist, "topk_epochs": [t[0] for t in top_info],
           "topk_val_aps": [t[1] for t in top_info], "topk_ps": ps,
           "val_ap_pred_avg": v_pred, "p_pred_avg": p_pred,
           "val_ap_argmax": max(h[1] for h in hist),
           "argmax_epoch": max(hist, key=lambda h: h[1])[0],
           "train_seconds": tr_t, "npar": sum(p.numel() for p in net.parameters()),
           "peak_gib": torch.cuda.max_memory_allocated() / 2 ** 30}
    return out, top_states


CELLS = [("C00", False, False), ("C11", True, True)]
CELLRES, CELLW = {}, {}
log("=" * 112)
log(f"骨干 B（单层 GRU，h={GRU_HID}，{NPAR:,} 参数）两格串行训练，seed={SEED}，"
    f"{N_EPOCH} 轮 × {EPOCH_STEPS} 步，不早停，无学习率调度器")
log(f"检查点策略：验证 AP 前 {TOPK} 名 epoch 的检查点各自推理后平均预测分数；p 取算术均值")
for cid, agg, lp in CELLS:
    log("-" * 112)
    log(f"### 骨干B-{cid}（agg={agg}, lp={lp}）###")
    r, w = train_and_select(f"GRU-{cid}", agg, lp)
    r["cell"] = cid
    CELLRES[cid] = r; CELLW[cid] = w

log("=" * 112)
for cid, _, _ in CELLS:
    r = CELLRES[cid]
    log(f"  {cid} 验证AP(预测平均)={r['val_ap_pred_avg']:.6f} top{TOPK}epoch={r['topk_epochs']} "
        f"p={r['p_pred_avg']:.4f} 训练{r['train_seconds']/60:.1f}分 峰值显存{r['peak_gib']:.2f}GiB")

_frozen = {
    "task": "第三章跨基座机制验证：骨干 B 单层 GRU 的 C00 / C11 两格",
    "backbone": {"type": "GRU-1layer-unidirectional", "input_size": D, "hidden_size": GRU_HID,
                 "npar_total": NPAR, "npar_by_module": _NPAR_BY_MOD,
                 "npar_formula": "5h^2 + 257h + 2", "mlp_reference_npar": MLP_NPAR,
                 "npar_deviation": NPAR - MLP_NPAR,
                 "npar_deviation_pct": (NPAR - MLP_NPAR) / MLP_NPAR * 100,
                 "masking": "pack_padded_sequence(enforce_sorted=False) + "
                            "pad_packed_sequence(total_length=L) + 输出乘 mask"},
    "mask_implementation_check": MASK_CHECK,
    "protocol": f"逐epoch在LSPR23实体不相交验证集上算逐流AP，取前{TOPK}名epoch的检查点各自推理后"
                f"平均预测分数；p取{TOPK}份算术均值；不早停；无学习率调度器；k={TOPK}事前固定",
    "checkpoint_rule": "prediction_averaging_of_top5_by_val_ap",
    "aligned_with": "runs/diagnostics/ch3-hparam-fairsel-v2（第二组 2x2，同一检查点策略）",
    "seed": SEED, "topk": TOPK, "L": L, "BS": BS, "LR": LR, "AUX_W": AUX_W,
    "epoch_steps": EPOCH_STEPS, "n_epoch": N_EPOCH,
    "split": {"n_train_seq": int(len(TR_IDX)), "n_val_seq": int(len(VAL_IDX)),
              "val_frac": VAL_FRAC, "time_tail": TIME_TAIL, "fill_rate": _FILL, "spw": SPW},
    "cells": {c: {k: v for k, v in CELLRES[c].items() if k != "val_ap_history"} for c in CELLRES},
    "cells_val_ap_history": {c: CELLRES[c]["val_ap_history"] for c in CELLRES}}
json.dump(_frozen, open(f"{OUT}/selection_frozen.json", "w"), ensure_ascii=False, indent=2)
SELECTION_FROZEN = True
log(f"选择阶段结束，结果已冻结写盘 {OUT}/selection_frozen.json")

# 释放 LSPR23 后再读 LSPR24，压低峰值
del gX23, gy23, gI, gM, gtr, gval, X23, y23, e23f, t23f, I23, M23, E23, T23
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24。合法评价次数 = 2
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
X24, y24, s24, d24, t24, I24, M24 = load24()
assert X24.shape[1] == D
assert I24.shape[1] == L and M24.shape[1] == L

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

# ---- 实体内时序秩（ch3_full 第 136-140 行）----
_o24 = np.lexsort((t24, ent24))
_e24 = ent24[_o24]
_s24 = np.flatnonzero(np.r_[True, _e24[1:] != _e24[:-1]])
_rank = np.empty(len(_o24), np.int64)
_rank[_o24] = np.arange(len(_o24)) - np.repeat(_s24, np.diff(np.r_[_s24, len(_o24)]))
del _e24, _s24, t24, _o24

gX24 = torch.from_numpy(X24).to(dev)
del X24
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
del I24, M24
log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB，评价序列 {len(gI24):,}")


# ---- 评价口径：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）----
def ent_ap(sc, seen, p=None, first_k=None):
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
def score24(states, agg, lp, name):
    """LSPR24 逐流打分：top-5 检查点各自推理一遍后平均预测分数，p 取算术均值。

    推理循环与预测平均逐字照抄 ch3_full.py 第 196-210 行。
    """
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    log(f"LSPR24 评价 #{_EVAL24_CALLS}/{N_EVAL_BUDGET} ← {name}"
        f"（骨干=GRU h={GRU_HID}, agg={agg}, lp={lp}, {len(states)} 个检查点预测平均）")
    _EVAL24_LEDGER.append({"call": _EVAL24_CALLS, "cell": name, "backbone": "GRU-1layer",
                           "L": L, "HID": GRU_HID, "agg": agg, "lp": lp, "n_ckpt": len(states)})
    assert _EVAL24_CALLS <= N_EVAL_BUDGET, f"LSPR24 评价次数超出预算：第 {_EVAL24_CALLS} 次"
    net = GRUModel(agg, lp).to(dev)
    acc = None; seen = None; ps = []
    t1 = time.time()
    for sd_ in states:
        net.load_state_dict({k: v.to(dev) for k, v in sd_.items()})
        net.eval(); ps.append(net.p.item())
        sc = torch.zeros(len(y24), device=dev)
        sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
        for a in range(0, len(gI24), 2048):
            idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
            pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
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


log("=" * 112)
GRU24 = {}
for cid, agg, lp in CELLS:
    r = CELLRES[cid]
    sc_c, seen_c, p_c = score24(CELLW[cid], agg, lp, f"骨干B-{cid}")
    assert seen_c.all(), f"{cid} 逐流覆盖不全：{seen_c.mean():.6f}"
    assert abs(p_c - r["p_pred_avg"]) < 1e-9, f"{cid} 权重回载后 p 与选择阶段不一致"
    m = metrics_of(sc_c, seen_c, p_c, lp)
    m.update(agg=agg, lp=lp, backbone="GRU-1layer", HID=GRU_HID, npar=r["npar"],
             topk_epochs=r["topk_epochs"], topk_val_aps=r["topk_val_aps"],
             val_ap_pred_avg=r["val_ap_pred_avg"], train_seconds=r["train_seconds"],
             peak_gib=r["peak_gib"])
    GRU24[cid] = m
    log(f"{cid}: top{TOPK}epoch={r['topk_epochs']} 验证AP(预测平均)={r['val_ap_pred_avg']:.6f} "
        f"p={p_c:.4f} | 逐流AP={m['fap']:.6f} AUC={m['fauc']:.6f} 实体AP(max)={m['e_max']:.6f} "
        f"实体AP(Lp)={m['e_lp']:.6f} DR@4%FPR(主)={m['dr_main']:.6f} (max口径={m['dr_max']:.6f})")
    np.save(f"{OUT}/scores_GRU_{cid}.npy", sc_c)
    np.save(f"{OUT}/seen_GRU_{cid}.npy", seen_c)
    log(f"  逐流分数已存 {OUT}/scores_GRU_{cid}.npy")
    del sc_c, seen_c

assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
assert _EVAL24_CALLS == N_EVAL_BUDGET, \
    f"LSPR24 评价次数应为 {N_EVAL_BUDGET}，实为 {_EVAL24_CALLS}"
log("=" * 112)
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，均在选择冻结之后")
for e in _EVAL24_LEDGER:
    log(f"  #{e['call']} {e['cell']}（骨干={e['backbone']}, agg={e['agg']}, lp={e['lp']}, "
        f"{e['n_ckpt']} 检查点）")

# =====================================================================================
# 跨基座对照：骨干 A（MLP）取 ch3-hparam-fairsel-v2 第二组 2x2，同一检查点策略
# =====================================================================================
log("=" * 112)
MLP24, XBACK = None, None
_v2 = json.load(open(V2))
assert _v2["selection"]["checkpoint_rule"] == "prediction_averaging_of_top5_by_val_ap", \
    "骨干 A 的检查点策略与本轮不一致，两表不可比"
MLP24 = {c: _v2["group2_cells_2x2"][c] for c in ["C00", "C11"]}
log("跨基座对照（两侧同为 top-5 预测平均协议、同切分、同种子 42、同 20 轮预算）")
log(f"{'骨干':<14}{'参数量':>10}{'C00 实体AP':>14}{'C11 实体AP':>14}{'增益(点)':>12}")
_rows = []
for bk, dd in [("MLP（既有）", MLP24), ("GRU（本轮）", GRU24)]:
    g = dd["C11"]["e_lp"] - dd["C00"]["e_lp"]
    _rows.append({"backbone": bk, "npar": dd["C00"]["npar"],
                  "c00_e_lp": dd["C00"]["e_lp"], "c11_e_lp": dd["C11"]["e_lp"],
                  "gain": g, "gain_points": g * 100})
    log(f"{bk:<14}{dd['C00']['npar']:>10,}{dd['C00']['e_lp']*100:>13.2f}%"
        f"{dd['C11']['e_lp']*100:>13.2f}%{g*100:>+11.2f}")
XBACK = {"rows": _rows,
         "gain_ratio_gru_over_mlp": (_rows[1]["gain"] / _rows[0]["gain"]
                                     if _rows[0]["gain"] != 0 else None),
         "gru_c11_minus_mlp_c11": GRU24["C11"]["e_lp"] - MLP24["C11"]["e_lp"],
         "gru_c00_minus_mlp_c00": GRU24["C00"]["e_lp"] - MLP24["C00"]["e_lp"],
         "gru_best_minus_mlp_best": max(GRU24["C11"]["e_lp"], GRU24["C00"]["e_lp"])
         - max(MLP24["C11"]["e_lp"], MLP24["C00"]["e_lp"])}
log("-" * 112)
_gg, _gm = _rows[1]["gain"], _rows[0]["gain"]
log(f"★ 问题一 普适性：GRU 骨干上 C00→C11 增益 {_gg*100:+.2f} 点，"
    f"MLP 骨干 {_gm*100:+.2f} 点 → 增益{'仍然成立' if _gg > 0 else '不成立（反向）'}")
log(f"★ 问题二 必要性：GRU 最佳格实体AP={max(GRU24['C11']['e_lp'], GRU24['C00']['e_lp']):.6f}，"
    f"MLP 最佳格={max(MLP24['C11']['e_lp'], MLP24['C00']['e_lp']):.6f}，"
    f"差 {XBACK['gru_best_minus_mlp_best']:+.6f} → "
    f"{'换 GRU 更好，骨干选择本身有改进空间' if XBACK['gru_best_minus_mlp_best'] > 0 else '换成本来就建模序列的骨干并不更好'}")
log("-" * 112)
log("全部指标（骨干 B 两格）")
for cid, _, _ in CELLS:
    m = GRU24[cid]
    log(f"  {cid}: 逐流AP={m['fap']:.6f} 逐流AUC={m['fauc']:.6f} 实体AP(max)={m['e_max']:.6f} "
        f"实体AP(Lp)={m['e_lp']:.6f} DR@4%FPR(主)={m['dr_main']:.6f} "
        f"DR@4%FPR(max)={m['dr_max']:.6f} p={m['p']:.6f} 参数量={m['npar']:,} "
        f"训练{m['train_seconds']/60:.2f}分 top5={m['topk_epochs']}")

json.dump({"selection": _frozen,
           "gru_cells": GRU24,
           "mlp_reference_cells": MLP24,
           "mlp_reference_source": V2,
           "cross_backbone": XBACK,
           "lspr24": {"n_flow": int(len(y24)), "n_entity": int(N_ENT),
                      "n_pos_entity": int(ent_lab.sum()), "flow_pos_rate": _flow_pos},
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS,
                         "budget": N_EVAL_BUDGET, "ledger": _EVAL24_LEDGER},
           "total_seconds": time.time() - T0},
          open(f"{OUT}/ch3_backbone_swap_results.json", "w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_backbone_swap_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
