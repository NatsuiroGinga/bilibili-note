# -*- coding: utf-8 -*-
"""第三章已发表基线的**等参数预算**重跑：GRU + 全注意力 Transformer + 一维 CNN，全量冻结缓存。

派生自 tools/ch3_baselines_full_neural.py。**训练配方逐字不变**，唯一改动是容量维度，
外加对三个架构**对称扩大**的学习率候选集合。

============================ 为什么补这一版 ============================
发表配置版的参数量与本章方法 CPA-ELP（90,242 参数）相差两个数量级：
  GRU 5,355,649（59×）、全注意力 Transformer 10,729,345（119×）、一维 CNN 34,529（0.38×）。
根 AGENTS.md 要求外部基线在同一「字段预算、标签权限、训练预算和评价指标」下重跑，
119 倍参数不满足同一训练预算。本文件把三个架构全部调到 90,242 的 ±10% 内，与发表配置版**并列**报告，
两版都进结果表，谁赢报谁。

============================ 等参数方案（预注册，跑前写死） ============================
选择规则（三个架构同一条，跑前固定，跑后不改）：
  保持发表配置的**深度、注意力头数、前馈扩张比、卷积核宽、池化宽度**不变，
  只对**宽度**做统一缩放；在整数与整除约束下取使 |P − 90,242| 最小的宽度。
  该规则对三个架构对称执行，**包括把偏小的一维 CNN 调大**，不允许只削赢过本方法的那两个。

  GRU（宽度 H，层数 6）
    P = 87H + 1 + 6·(6H² + 6H)
    校验：H=384 → 5,355,649，与发表配置逐位相同
    选 H=48（= 384/8，宽度缩放 1/8）→ 88,849，偏差 −1.54%，**调小**
    邻域：H=47 → 85,306（−5.47%）；H=49 → 92,464（+2.46%）

  全注意力 Transformer（宽度 H，层数 6，头数 8，前馈 4H）
    P = 215H + 1 + 6·(4H² + 9H + 2H·FFN + FFN)
    校验：H=384, FFN=1536 → 10,729,345，与发表配置逐位相同
    选 H=32（= 384/12，宽度缩放 1/12）、FFN=128、nhead=8（头维 4）→ 83,105，偏差 −7.91%，**调小**
    邻域：H=24 → 48,505（−46.25%）；H=40 → 126,921（+40.65%）。
    头数 8 要求 H 被 8 整除，故 ±10% 区间内 H=32 是唯一可行解，−7.91% 是该架构能达到的最小偏差。

  一维 CNN（通道 C1/C2、全连接宽 FC，统一缩放系数 s：C1=16s, C2=32s, FC=64s，池化恒 16）
    P = 4C1 + (3·C1·C2 + C2) + (C2·16·FC + FC) + (FC + 1)
    校验：s=1 → 34,529，与发表配置逐位相同
    选 s=1.625 → C1=26, C2=52, FC=104 → 90,949，偏差 +0.78%，**调大**
    邻域：s=1.5625 → 84,101（−6.81%）；s=1.6875 → 98,065（+8.67%）

============================ 学习率：同一套选择规则，对称扩大候选 ============================
发表配置版每架构训 2 档学习率（各自论文/Q0 值 + 本章 2e-3），按 LSPR23 验证集 top-5 预测平均 AP 择优。
本版**保留同一条选择规则**，但把候选集合对三个架构**对称扩大**为同一网格：
    LR_GRID = {3e-4, 1e-3, 2e-3, 5e-3}
  为什么扩大：三个架构都被压到约 90K 参数，而 3e-4（Dijk 2026/Q0）与 1e-3（Leoste 2025）
  是在 10–100 倍容量下定的，小模型最优学习率通常更大。若沿用原来每架构 2 档，
  测到的可能是学习率不适配而不是容量效应，构成人为削弱基线。
  为什么这样扩大是安全的：候选集合是取最大，扩大候选只会抬高（不会压低）每个基线的择优结果，
  且三个架构用**完全相同**的四点网格，不存在给某个架构开小灶。
  该网格是原候选的超集：GRU/Transformer 原 {3e-4, 2e-3} ⊂ 网格，CNN 原 {1e-3, 2e-3} ⊂ 网格。
共 3 架构 × 4 学习率 = 12 次训练，每次 20 epoch × 1000 步。

============================ 与发表配置版逐字相同的部分 ============================
优化器 AdamW(weight_decay=0.01) 均匀施加、梯度裁剪 1.0、种子 42、BS=64、L=128、
20 epoch × 1000 步不早停、逐流 pos_weight、检查点 top-5 预测平均、
LSPR23 实体不相交验证划分（RandomState(42)，150,680 实体 / 208,598 训练 / 22,444 验证）、
数据加载与序列构造、评价代码、实体聚合、DR@4%FPR 阈值取法、推理批大小、fp32、83 字段预算。

============================ LSPR24 隔离 ============================
  guarded_load() 是所有 np.load 的唯一入口，名字含 "24" 且 SELECTION_FROZEN 为假时断言失败。
  十二次训练与择优全部完成 → selection_frozen_neural.json 落盘 → SELECTION_FROZEN=True
  → 才允许读 LSPR24。score24() 每架构调用一次，本进程合法总次数 == 3。
  train_and_select() / val_scores() 函数体内不出现任何 LSPR24 标识符。

评价口径逐字复刻 ch3_full.py：实体构造 130-133、ent_ap 213-225、dr_at_fpr 236-240。
主表一律用 max 聚合；额外报「借用本章 p=1.0562171936035156 的 Lp 聚合」作敏感性参照。
不创建 SwanLab 运行身份（与 ch3_baselines_full_neural.py 一致）。

容量自检入口：CH3_PM_CAPACITY_PROBE=1 时只打印解析公式值与 torch 实测参数量后退出，
不读任何数据、不创建运行身份、不触碰 LSPR24。
"""

import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-param-matched"
os.makedirs(OUT, exist_ok=True)

# ---- 训练预算：与 ch3_baselines_full_neural.py 逐字相同 ----
SEED, BS, L = 42, 64, 128
EPOCH_STEPS, N_EPOCH, TOPK = 1000, 20, 5
VAL_FRAC, TIME_TAIL = 0.10, 0.15
TARGET_FPR = 0.04
P_BORROW = 1.0562171936035156
WEIGHT_DECAY, GRAD_CLIP = 0.01, 1.0
DROPOUT = 0.1
D = 83                      # 字段预算（Dijk 2026 附录 A 口径），运行时对 X23/X24 再断言一次

# ---- 等参数容量维度（预注册，见文件头）----
TARGET_PARAMS = 90242       # 本章方法 CPA-ELP 的参数量
PARAM_TOL = 0.10            # 允许偏差 ±10%
HID_GRU, NLAYER_GRU = 48, 6
HID_TF, NLAYER_TF, NHEAD_TF, FFN_TF = 32, 6, 8, 128
CNN_C1, CNN_C2, CNN_POOL, CNN_FC = 26, 52, 16, 104

# ---- 学习率：对三个架构对称的同一四点网格（原候选的超集）----
LR_GRID = [3e-4, 1e-3, 2e-3, 5e-3]
ARCHS = [
    ("gru_dijk2026_pm90k", "GRU（Dijk 2026 循环骨干，等参数90K）", "循环", LR_GRID, 1024),
    ("transformer_dijk2026_pm90k", "全注意力Transformer（Dijk 2026 注意力骨干，等参数90K）",
     "注意力", LR_GRID, 512),
    ("cnn_leoste2025_pm90k", "一维CNN（Leoste 2025 卷积，等参数90K）", "卷积", LR_GRID, 512),
]

# ---- 解析参数量公式：先对发表配置逐位复核，再给出等参数解 ----
def formula_gru(hid, nlayer):
    return 87 * hid + 1 + nlayer * (6 * hid * hid + 6 * hid)


def formula_tf(hid, nlayer, ffn):
    return 215 * hid + 1 + nlayer * (4 * hid * hid + 9 * hid + 2 * hid * ffn + ffn)


def formula_cnn(c1, c2, pool, fc):
    return 4 * c1 + (3 * c1 * c2 + c2) + (c2 * pool * fc + fc) + (fc + 1)


CAPACITY = {
    "gru_dijk2026_pm90k": {
        "formula": "P = 87H + 1 + NL·(6H² + 6H)",
        "published_dims": {"hidden": 384, "num_layers": 6},
        "published_params": 5355649,
        "dims": {"hidden": HID_GRU, "num_layers": NLAYER_GRU},
        "formula_params": formula_gru(HID_GRU, NLAYER_GRU),
        "direction": "调小", "width_scale": HID_GRU / 384},
    "transformer_dijk2026_pm90k": {
        "formula": "P = 215H + 1 + NL·(4H² + 9H + 2H·FFN + FFN)",
        "published_dims": {"hidden": 384, "num_layers": 6, "nhead": 8, "ffn": 1536},
        "published_params": 10729345,
        "dims": {"hidden": HID_TF, "num_layers": NLAYER_TF, "nhead": NHEAD_TF, "ffn": FFN_TF},
        "formula_params": formula_tf(HID_TF, NLAYER_TF, FFN_TF),
        "direction": "调小", "width_scale": HID_TF / 384},
    "cnn_leoste2025_pm90k": {
        "formula": "P = 4C1 + (3·C1·C2 + C2) + (C2·POOL·FC + FC) + (FC + 1)",
        "published_dims": {"c1": 16, "c2": 32, "pool": 16, "fc": 64},
        "published_params": 34529,
        "dims": {"c1": CNN_C1, "c2": CNN_C2, "pool": CNN_POOL, "fc": CNN_FC},
        "formula_params": formula_cnn(CNN_C1, CNN_C2, CNN_POOL, CNN_FC),
        "direction": "调大", "width_scale": CNN_C1 / 16},
}
for _k, _v in CAPACITY.items():
    _v["deviation_pct"] = 100.0 * (_v["formula_params"] - TARGET_PARAMS) / TARGET_PARAMS

assert formula_gru(384, 6) == 5355649, "GRU 参数量公式未能复现发表配置"
assert formula_tf(384, 6, 1536) == 10729345, "Transformer 参数量公式未能复现发表配置"
assert formula_cnn(16, 32, 16, 64) == 34529, "CNN 参数量公式未能复现发表配置"

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
# 三个架构：拓扑逐字复刻 ch3_baselines_full_neural.py 第 163-234 行，
# 唯一改动是把共享的 HID/NLAYER/NHEAD/FFN 换成上面的等参数容量维度。
# =====================================================================================
class PerFlowInputProjection(nn.Module):
    def __init__(self, hid):
        super().__init__()
        self.projection = nn.Sequential(nn.Linear(D, hid), nn.LayerNorm(hid), nn.GELU())

    def forward(self, values):
        return self.projection(values)


class DijkGruClassifier(nn.Module):
    """Dijk 2026 循环骨干，宽度缩到等参数预算。"""

    def __init__(self):
        super().__init__()
        self.input_projection = PerFlowInputProjection(HID_GRU)
        self.encoder = nn.GRU(HID_GRU, HID_GRU, num_layers=NLAYER_GRU, dropout=DROPOUT,
                              batch_first=True)
        self.classifier = nn.Linear(HID_GRU, 1)

    def forward(self, values, valid):
        encoded, _ = self.encoder(self.input_projection(values))
        return self.classifier(encoded).squeeze(-1).masked_fill(~valid, 0.0)


class DijkFullAttentionClassifier(nn.Module):
    """Dijk 2026 BERT 式全注意力骨干，宽度缩到等参数预算。"""

    def __init__(self):
        super().__init__()
        self.input_projection = PerFlowInputProjection(HID_TF)
        self.position = nn.Parameter(torch.zeros(1, L, HID_TF))
        layer = nn.TransformerEncoderLayer(
            d_model=HID_TF, nhead=NHEAD_TF, dim_feedforward=FFN_TF, dropout=DROPOUT,
            activation="gelu", batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=NLAYER_TF,
                                             enable_nested_tensor=False)
        self.classifier = nn.Linear(HID_TF, 1)

    def forward(self, values, valid):
        length = values.shape[1]
        encoded = self.input_projection(values) + self.position[:, :length]
        encoded = self.encoder(encoded, src_key_padding_mask=~valid)
        return self.classifier(encoded).squeeze(-1).masked_fill(~valid, 0.0)


class LeosteNearestTextCnnClassifier(nn.Module):
    """Leoste 2025 卷积拓扑，通道与全连接宽度**放大**到等参数预算。"""

    def __init__(self):
        super().__init__()
        self.convolutions = nn.Sequential(
            nn.Conv1d(1, CNN_C1, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv1d(CNN_C1, CNN_C2, kernel_size=3, padding=1), nn.ReLU(),
            nn.AdaptiveMaxPool1d(CNN_POOL))
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(DROPOUT), nn.Linear(CNN_C2 * CNN_POOL, CNN_FC), nn.ReLU(),
            nn.Linear(CNN_FC, 1))

    def forward(self, values, valid):
        batch, length, width = values.shape
        flattened = values.reshape(batch * length, 1, width)
        logits = self.classifier(self.convolutions(flattened)).reshape(batch, length)
        return logits.masked_fill(~valid, 0.0)


def build(key):
    if key == "gru_dijk2026_pm90k":
        return DijkGruClassifier()
    if key == "transformer_dijk2026_pm90k":
        return DijkFullAttentionClassifier()
    if key == "cnn_leoste2025_pm90k":
        return LeosteNearestTextCnnClassifier()
    raise ValueError(f"未知神经基线：{key}")


def capacity_report():
    """torch 实测参数量 vs 解析公式 vs 90,242 目标；三者不一致立即失败。"""
    log("=" * 112)
    log(f"等参数容量自检：目标 {TARGET_PARAMS:,} 参数，允许偏差 ±{PARAM_TOL*100:.0f}%")
    rows = []
    for key, display, family, lrs, ibs in ARCHS:
        cap = CAPACITY[key]
        npar = sum(p.numel() for p in build(key).parameters())
        assert npar == cap["formula_params"], \
            f"{key} torch 实测 {npar} 与公式 {cap['formula_params']} 不一致"
        dev = 100.0 * (npar - TARGET_PARAMS) / TARGET_PARAMS
        assert abs(dev) <= PARAM_TOL * 100 + 1e-9, f"{key} 偏差 {dev:+.2f}% 超出 ±10%"
        cap["torch_params"] = int(npar)
        rows.append((display, cap, npar, dev))
        log(f"  {display}")
        log(f"    公式 {cap['formula']}")
        log(f"    发表配置 {cap['published_dims']} → {cap['published_params']:,} 参数")
        log(f"    等参数维度 {cap['dims']}（宽度缩放 {cap['width_scale']:.4f}，{cap['direction']}）")
        log(f"    torch 实测 {npar:,} 参数，相对 {TARGET_PARAMS:,} 偏差 {dev:+.2f}%")
    return rows


if os.environ.get("CH3_PM_CAPACITY_PROBE") == "1":
    capacity_report()
    log("容量自检通过（未读入任何数据，未触碰 LSPR24）")
    sys.exit(0)

# =====================================================================================
# 阶段一：只读入 LSPR23
# =====================================================================================
capacity_report()
log("=" * 112)
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
X23 = guarded_load("X23")
y23 = guarded_load("y23")
I23 = guarded_load("I23")
M23 = guarded_load("M23")
E23 = guarded_load("E23")
T23 = guarded_load("T23")
assert X23.shape[1] == D, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {X23.shape[1]}"
assert X23.shape[0] == 16_353_511, f"LSPR23 全量流数自检失败：{X23.shape[0]}"
log(f"LSPR23 流={len(y23):,} 特征数={D} L=128 冻结序列={len(I23):,}")

dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "本任务必须在 GPU 上运行"
log(f"torch {torch.__version__} | {torch.cuda.get_device_name(0)}")

# ---- 验证划分：逐字复用 tools/ch3_2x2_fairsel.py 第 79-94 行（RandomState(42)，非 default_rng）----
rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut                                                 # 时间尾部（不作选择信号）
tr_idx = np.flatnonzero(~(m_ent | m_time))
val_idx = np.flatnonzero(m_ent & ~m_time)
assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
assert len(uent) == 150680, f"LSPR23 实体数自检失败：{len(uent)}"
assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
assert len(val_idx) == 22444, f"实体不相交验证序列数自检失败：{len(val_idx)}"
log("切分自检通过：150,680 实体 / 208,598 训练序列 / 22,444 验证序列，与 ch3_2x2_fairsel 一致")
del m_ent, m_time, E23, T23

gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev)
gval = torch.from_numpy(val_idx).to(dev)
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# ---- 逐流 pos_weight：口径照抄 ch3_full.py 第 170 行，用全量 LSPR23 ----
_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(pos_weight=_pos)
log(f"逐流 pos_weight={_pos.item():.6f}（Q0 用 negative/positive，与本式同值）")


@torch.no_grad()
def val_scores(net, ibs):
    """LSPR23 实体不相交验证集上的逐流预测与标签（顺序对所有检查点一致，可逐元素平均）。

    本函数是唯一的模型选择信号来源，只触碰 gX23/gy23/gI23/gM23/gval。
    """
    was_training = net.training
    net.eval(); P = []; Y = []
    for a in range(0, len(val_idx), ibs):
        sel = gval[a:a + ibs]; idx = gI23[sel]; msk = gM23[sel] > 0.5; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
        fm = msk.reshape(-1)
        P.append(torch.sigmoid(lo).reshape(-1)[fm].float().cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    if was_training:
        net.train()
    return np.concatenate(P), np.concatenate(Y)


def train_and_select(key, display, lr, ibs):
    """训练满 20 epoch 不早停，逐 epoch 记录验证 AP，取前 5 名 epoch 做**预测平均**。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    tag = f"{display} lr={lr:g}"
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = build(key).to(dev)
    npar = sum(p.numel() for p in net.parameters())
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    gen = torch.Generator().manual_seed(SEED)
    hist, snaps = [], []
    t0 = time.time()
    net.train()
    for ep in range(1, N_EPOCH + 1):
        te = time.time()
        for st in range(EPOCH_STEPS):
            sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=gen).to(dev)]
            idx = gI23[sel]; msk = gM23[sel] > 0.5
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            lo = net(xb, msk)
            loss = _lf(lo[msk], yb[msk])
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP); opt.step()
            if ep == 1 and (st + 1) % 250 == 0:
                el = time.time() - te
                log(f"    {tag} ep1 步 {st+1}/{EPOCH_STEPS} loss={float(loss):.6f} "
                    f"{el/(st+1)*1000:.1f} ms/步 → 全程预计 "
                    f"{el/(st+1)*EPOCH_STEPS*N_EPOCH/60:.1f} 分")
        v, _y = val_scores(net, ibs)
        vap = float(average_precision_score(_y, v))
        hist.append([ep, vap])
        snaps.append({k: t.detach().cpu().clone() for k, t in net.state_dict().items()})
        log(f"    {tag} ep {ep:>2}/{N_EPOCH} 验证AP={vap:.6f} 本轮{(time.time()-te)/60:.2f}分 "
            f"累计{(time.time()-t0)/60:.1f}分")
    tr_t = time.time() - t0

    # ---- top-5 预测平均：k 事前固定，排序键 (-验证AP, epoch)，同分取更早的 epoch ----
    rank = sorted(range(N_EPOCH), key=lambda i: (-hist[i][1], hist[i][0]))
    top = sorted(rank[:TOPK])
    top_states = [snaps[i] for i in top]
    Pacc, Yv = None, None
    for sd_ in top_states:
        net.load_state_dict({k: t.to(dev) for k, t in sd_.items()})
        P_, Y_ = val_scores(net, ibs)
        Pacc = P_ if Pacc is None else Pacc + P_
        Yv = Y_ if Yv is None else Yv
    assert Yv.max() > 0, "验证集无正例，选择信号无效"
    v_pred = float(average_precision_score(Yv, Pacc / len(top_states)))
    top_info = [[hist[i][0], hist[i][1]] for i in top]
    log(f"  {tag} 训练 {tr_t/60:.2f} 分 参数量 {npar:,} | top{TOPK} epoch="
        f"{[t[0] for t in top_info]} → 预测平均验证AP={v_pred:.6f} "
        f"（逐epoch最好 {max(h[1] for h in hist):.6f}）")
    del net
    torch.cuda.empty_cache()
    return {"key": key, "display_name": display, "lr": lr, "npar": npar,
            "val_ap_history": hist, "topk_epochs": [t[0] for t in top_info],
            "topk_val_aps": [t[1] for t in top_info], "val_ap_pred_avg": v_pred,
            "val_ap_argmax": max(h[1] for h in hist), "train_seconds": tr_t,
            "peak_gib": torch.cuda.max_memory_allocated() / 2 ** 30}, top_states


SEL, TOPW = {}, {}
log("=" * 112)
log(f"三个架构 × {len(LR_GRID)} 档学习率 = {3*len(LR_GRID)} 次训练，每次 {N_EPOCH} epoch × "
    f"{EPOCH_STEPS} 步 = {N_EPOCH*EPOCH_STEPS:,} 步，BS={BS}，L={L}，不早停")
log(f"学习率网格（三个架构完全相同）：{[f'{x:g}' for x in LR_GRID]}")
for key, display, family, lrs, ibs in ARCHS:
    log("=" * 112)
    log(f"--- {display}（{family}族）---")
    cands = []
    for lr in lrs:
        r, w = train_and_select(key, display, lr, ibs)
        cands.append(r)
        TOPW[(key, lr)] = w
    best = max(cands, key=lambda r: (r["val_ap_pred_avg"], -r["lr"]))
    SEL[key] = {"family": family, "display_name": display, "infer_bs": ibs,
                "candidates": cands, "chosen_lr": best["lr"], "chosen": best}
    log(f"  ★ {display} 学习率择优（只用 LSPR23 验证集）："
        + "  ".join(f"lr={c['lr']:g}→{c['val_ap_pred_avg']:.6f}" for c in cands)
        + f"  ⇒ 选 lr={best['lr']:g}")
    for lr in lrs:
        if lr != best["lr"]:
            del TOPW[(key, lr)]

# =====================================================================================
# 阶段闸门：先把选择结果写盘冻结，再允许读入 LSPR24
# =====================================================================================
_frozen = {
    "protocol": "等参数预算（90,242±10%）版：逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，"
                "取前 5 名 epoch 的预测平均；学习率在对三个架构对称的四点网格 "
                "{3e-4, 1e-3, 2e-3, 5e-3} 中按同一验证信号择优；LSPR24 不参与选择",
    "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "batch_size": BS,
    "sequence_length": L, "topk": TOPK, "weight_decay": WEIGHT_DECAY,
    "grad_clip": GRAD_CLIP, "field_budget": D,
    "target_params": TARGET_PARAMS, "param_tolerance": PARAM_TOL, "capacity": CAPACITY,
    "lr_grid": LR_GRID,
    "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
    "architectures": {k: {kk: vv for kk, vv in v.items() if kk != "chosen"}
                      for k, v in SEL.items()}}
json.dump(_frozen, open(f"{OUT}/selection_frozen_neural.json", "w"), ensure_ascii=False,
          indent=2, default=str)
SELECTION_FROZEN = True
log("=" * 112)
log(f"选择阶段结束，结果已冻结写盘 {OUT}/selection_frozen_neural.json")
for k in SEL:
    log(f"  {SEL[k]['display_name']}: 选中 lr={SEL[k]['chosen_lr']:g} "
        f"top{TOPK}epoch={SEL[k]['chosen']['topk_epochs']} "
        f"验证AP={SEL[k]['chosen']['val_ap_pred_avg']:.6f}")

del gX23, gy23, gI23, gM23, gtr, gval, X23, y23, I23, M23
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，每个架构只评价一次
# =====================================================================================


def load24():
    global _N24_LOADS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
    _N24_LOADS += 1
    assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
    return (guarded_load("X24"), guarded_load("y24"), guarded_load("s24", True),
            guarded_load("d24", True), guarded_load("I24"), guarded_load("M24"))


log("=" * 112)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
X24, y24, s24, d24, I24, M24 = load24()
assert X24.shape[1] == D
assert X24.shape[0] == 20_227_356, f"LSPR24 全量流数自检失败：{X24.shape[0]}"

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-133 行 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 流={len(y24):,} 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} "
    f"逐流正例率={_flow_pos:.10f}")
assert N_ENT == 47115, f"LSPR24 实体数自检失败：{N_ENT}"
assert int(ent_lab.sum()) == 752, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(_flow_pos - 0.0257073138) < 1e-9, f"LSPR24 逐流正例率自检失败：{_flow_pos:.12f}"
log("LSPR24 自检通过：实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138")
del key24, s24, d24

gX24 = torch.from_numpy(X24).to(dev)
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
del X24, I24, M24
log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB，序列 {len(gI24):,}")


# ---- 评价口径：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）----
def ent_ap(sc, seen, p=None):
    m = seen
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), int(ok.sum())


def dr_at_fpr(sc, seen, target=TARGET_FPR, p=None):
    m = seen
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


@torch.no_grad()
def score24(key, states, ibs):
    """LSPR24 逐流打分：top-5 检查点各自推理一遍后**平均预测分数**。

    推理循环与预测平均逐字照抄 ch3_full.py 第 196-210 行。
    每调用一次记一次评价；本进程合法总次数 == 3。
    """
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    _EVAL24_LEDGER.append({"call": _EVAL24_CALLS, "group": "神经模型族（等参数90K）",
                           "model": key, "n_ckpt": len(states)})
    assert _EVAL24_CALLS <= 3, f"本进程 LSPR24 评价次数超出预算：第 {_EVAL24_CALLS} 次"
    log(f"LSPR24 评价 #{_EVAL24_CALLS}/3 ← {SEL[key]['display_name']}"
        f"（lr={SEL[key]['chosen_lr']:g}，{len(states)} 个检查点预测平均）")
    net = build(key).to(dev)
    acc = None; seen = None
    t1 = time.time()
    for ci, sd_ in enumerate(states):
        net.load_state_dict({k: t.to(dev) for k, t in sd_.items()})
        net.eval()
        sc = torch.zeros(len(y24), device=dev)
        sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
        for a in range(0, len(gI24), ibs):
            idx = gI24[a:a + ibs]; msk = gM24[a:a + ibs] > 0.5; b = idx.shape[0]
            pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
            fi = idx.reshape(-1); fm = msk.reshape(-1)
            sc[fi[fm]] = pr.reshape(-1)[fm].float(); sn[fi[fm]] = True
        s_ = sc.cpu().numpy(); n_ = sn.cpu().numpy()
        acc = s_ if acc is None else acc + s_
        seen = n_ if seen is None else (seen | n_)
        del sc, sn
        log(f"    检查点 {ci+1}/{len(states)} 推理完成，累计 {time.time()-t1:.0f}s")
    del net
    torch.cuda.empty_cache()
    return acc / len(states), seen


def metrics_of(sc, seen):
    e_max, n_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, P_BORROW)
    return {"flow_ap": float(average_precision_score(y24[seen], sc[seen])),
            "flow_auc": float(roc_auc_score(y24[seen], sc[seen])),
            "ent_ap_max": float(e_max), "ent_ap_lp_borrowed": float(e_lp),
            "dr_at_fpr_max": float(dr_at_fpr(sc, seen, TARGET_FPR, None)),
            "dr_at_fpr_lp_borrowed": float(dr_at_fpr(sc, seen, TARGET_FPR, P_BORROW)),
            "n_ent_scored": int(n_ok), "coverage": float(seen.mean())}


RES = {}
for key, display, family, lrs, ibs in ARCHS:
    ch = SEL[key]["chosen"]
    sc, seen = score24(key, TOPW[(key, ch["lr"])], ibs)
    assert seen.all(), f"{key} 逐流覆盖不全：{seen.mean():.6f}（冻结 I24/M24 应恒为 1.0）"
    np.save(f"{OUT}/scores_{key}.npy", sc)
    RES[key] = {"display_name": display, "family": family, "chosen_lr": ch["lr"],
                "npar": ch["npar"], "train_seconds": ch["train_seconds"],
                "topk_epochs": ch["topk_epochs"], "val_ap_pred_avg": ch["val_ap_pred_avg"],
                "capacity": CAPACITY[key],
                "param_deviation_pct": CAPACITY[key]["deviation_pct"],
                "scale": f"{ch['npar']:,} 参数", **metrics_of(sc, seen)}
    r = RES[key]
    log(f"{display}: 逐流AP={r['flow_ap']:.6f} AUC={r['flow_auc']:.6f} "
        f"实体AP(max)={r['ent_ap_max']:.6f} DR@4%FPR(max)={r['dr_at_fpr_max']:.6f} "
        f"| 实体AP(Lp借用)={r['ent_ap_lp_borrowed']:.6f} "
        f"DR@4%FPR(Lp借用)={r['dr_at_fpr_lp_borrowed']:.6f}")
    del sc, seen

assert _EVAL24_CALLS == 3, f"本进程 LSPR24 评价次数应为 3，实为 {_EVAL24_CALLS}"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
log("=" * 112)
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，均在选择冻结之后")

W = 128
log("=" * W)
log("神经模型族**等参数预算**基线在 LSPR24 全量上的结果（主口径 = max 聚合）")
log(f"{'基线':<46}{'架构族':<8}{'逐流AP':>11}{'实体AP(max)':>13}{'DR@4%FPR(max)':>15}"
    f"{'实体AP(Lp借用)':>16}{'训练用时':>10}{'参数量':>10}{'偏差':>9}")
for key, display, family, lrs, ibs in ARCHS:
    r = RES[key]
    log(f"{display:<46}{family:<8}{r['flow_ap']:>11.6f}{r['ent_ap_max']:>13.6f}"
        f"{r['dr_at_fpr_max']:>15.6f}{r['ent_ap_lp_borrowed']:>16.6f}"
        f"{r['train_seconds']/60:>9.2f}分{r['npar']:>10,}{r['param_deviation_pct']:>8.2f}%")
log("=" * W)

json.dump({"protocol": _frozen["protocol"], "seed": SEED, "field_budget": D,
           "target_params": TARGET_PARAMS, "param_tolerance": PARAM_TOL,
           "capacity": CAPACITY, "lr_grid": LR_GRID,
           "p_borrowed_for_lp_sensitivity": P_BORROW, "target_fpr": TARGET_FPR,
           "budget": {"n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "batch_size": BS,
                      "sequence_length": L, "topk": TOPK},
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "n_test_flows": int(len(y24)),
           "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                      "flow_pos_rate": _flow_pos},
           "models": RES,
           "lr_selection": {k: {"chosen_lr": SEL[k]["chosen_lr"],
                                "candidates": [{"lr": c["lr"],
                                                "val_ap_pred_avg": c["val_ap_pred_avg"],
                                                "val_ap_argmax": c["val_ap_argmax"],
                                                "train_seconds": c["train_seconds"]}
                                               for c in SEL[k]["candidates"]]} for k in SEL},
           "val_ap_history": {k: {str(c["lr"]): c["val_ap_history"]
                                  for c in SEL[k]["candidates"]} for k in SEL},
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS,
                         "ledger": _EVAL24_LEDGER}},
          open(f"{OUT}/neural_results.json", "w"), ensure_ascii=False, indent=2, default=str)
log(f"神经模型族等参数结果已存 {OUT}/neural_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
