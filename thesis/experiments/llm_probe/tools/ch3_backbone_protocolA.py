# -*- coding: utf-8 -*-
"""第三章基座对照（协议 A）：GRU / Transformer / 一维 CNN / RWKV-7 时间混合块各跑完整 2x2 四格。

本文件由 tools/ch3_2x2_fairsel.py **逐字复制**后只改四类内容：
  1. Model 内部的编码器：加 BACKBONE 开关，支持 'mlp'（原样）/'gru'/'transformer'/'cnn'/'rwkv7'
  2. 各骨干的隐藏维（为对齐 MLP 的 90,242 参数预算）
  3. OUT 输出目录与运行身份字符串
  4. 遍历骨干所需的最小外层循环
切分代码、val_ap()、train_and_select() 的训练循环/优化器/损失/AUX_W/梯度裁剪/best 更新、
阶段闸门顺序、LSPR24 评价与指标计算（含 float32 对齐）、
SEED / N_EPOCH / EPOCH_STEPS / BS / lr / VAL_FRAC / AUX_W / L 与全部隔离断言均保持原样。
（另有一处纯报告删除：原脚本末尾「与冻结协议末 5 平均逐格对比」只对 MLP 有对照数字，
  其余骨干没有末 5 平均的冻结制品，故整段移除；它不参与训练、选择、闸门与任何指标计算。）

协议 A 定义（与 ch3_2x2_fairsel.py 完全一致）：
  逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取 AP 最大的那个**单个** epoch 的检查点，
  不做任何平均、不早停、训满 20 epoch。（协议 B 的 top-5 预测平均不在本脚本内，也未参照。）

MLP 骨干不在本脚本重跑；其协议 A 四格数字在阶段二从冻结制品
runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json 只读读取并硬校验。

五个骨干全部预注册、全部照报，不看结果后回头改骨干选择、隐藏维、指标或口径。

============================ LSPR24 隔离保证（本任务的核心）============================
不是靠注释约定，是靠**加载顺序**与**机械断言**：

  阶段一「选择」：进程内只从磁盘读入 LSPR23（X23/y23/I23/M23/E23/T23）。
                  四骨干共十六格全部训练完，逐 epoch 只在 LSPR23 验证集上打分并选出 epoch，
                  随后把「每格选中的 epoch + 该 epoch 的验证 AP」写盘冻结。
                  此刻 LSPR24 的任何数组**根本不存在于本进程**——没有 open()，没有 np.load()。
  阶段闸门      ：SELECTION_FROZEN = True，且 selection_frozen.json 已落盘。
  阶段二「评价」：LSPR24 的 np.load 之前先断言 SELECTION_FROZEN。
                  score24() 首行同样断言，并对每格计数，最后断言总评价次数 == 16。
                  MLP 参照 JSON（含 LSPR24 指标）同样只在闸门之后读取。

  训练/选择函数 train_and_select() 的函数体内不出现任何 24 相关标识符；
  它只能访问模块级的 gX23/gy23/gI23/gM23/gtr/gval。
=====================================================================================
"""

import json
import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-backbone-protocolA"
MLP_REF = ("/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/"
           "ch3-2x2-fairsel/ch3_2x2_fairsel_results.json")
RUN_ID = "ch3-backbone-protocolA-gru-transformer-cnn-rwkv7-2x2-seed42-v1"
os.makedirs(OUT, exist_ok=True)

# ---- 超参：逐字照抄 ch3_full.py 第 52、106-107 行 ----
L, BS, HID = 128, 64, 192
SEED, AUX_W = 42, 1.0
EPOCH_STEPS = 1000
N_EPOCH = 20                      # 20 epoch × 1000 步 = 20000 步，与冻结预算相同
# ---- 验证划分：逐字照抄 select_signal.py 第 103 行 ----
VAL_FRAC, TIME_TAIL = 0.10, 0.15

# ---- 骨干隐藏维（唯一新增的超参，只为对齐 MLP 的 90,242 参数预算）----
MLP_NPAR = 90242
GRU_HID = 111                     # 5h² + (3D+8)h + 2 = 90,134，偏 -0.120%
TR_D, TR_HEADS = 77, 7            # 6d² + 2·d·ff + ff + (D+12)d + 2 = 90,631，偏 +0.431%；head_dim = 11
TR_FF = 4 * TR_D                  # 标准 4× 前馈宽度 = 308
CNN_C, CNN_K, CNN_LAYERS = 92, 3, 3   # (2k+2)c² + (kD+5)c + 2 = 91,082，偏 +0.931%
RWKV_C, RWKV_HEAD, RWKV_LORA = 112, 16, 8   # 6C² + 6·C·lora + (D+16)C + 2 = 91,730，偏 +1.649%
BACKBONES = ["gru", "transformer", "cnn", "rwkv7"]

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
log(f"运行身份 {RUN_ID}")
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
# 数据身份：X23/X24 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和
# 标准差标准化 → 裁剪 [-10, 10]），不是 raw83 原值；形状、dtype 与文件字节数都与 raw83 产品相同
# 但内容不同。只有训练侧同样消费这份缓存的模型才可直接用。见该缓存目录的 README.md。
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


# ---- 模型与损失：逐字照抄 ch3_full.py 第 150-172 行；仅 Model 内部编码器加骨干开关 ----
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


def npar_formula(backbone):
    """解析参数量公式；与 torch 实测逐项核对。

    mlp        ：f(Dh+h) + g(2h²+h) + o(h+1) + p_log(1)          = 2h² + (D+3)h + 2
    gru        ：GRU(3h²+3Dh+6h) + g(2h²+h) + o(h+1) + p_log(1)  = 5h² + (3D+8)h + 2
    transformer：inp(Dd+d) + MHA(4d²+4d) + 2×LN(4d)
                 + FFN(2·d·ff + ff + d) + g(2d²+d) + o(d+1) + p_log(1)
               = 6d² + 2·d·ff + ff + (D+12)d + 2
    cnn        ：conv1(kDc+c) + (n-1)×conv(kc²+c) + g(2c²+c) + o(c+1) + p_log(1)
               = (k(n-1)+2)c² + (kD + n + 2)c + 2      本脚本 n=3, k=3
    rwkv7      ：inp(DC+C)
                 + 块内向量 13C（x_r/x_w/x_k/x_v/x_a/x_g 各 C，w0、a0、k_k、k_a、r_k 各 C，ln_x 权重与偏置 2C）
                 + 三组 LoRA 6·C·lora（w1/w2、a1/a2、g1/g2）
                 + r/k/v/output 四个无偏置方阵 4C²
                 + g(2C²+C) + o(C+1) + p_log(1)
               = 6C² + 6·C·lora + (D+16)C + 2
      单块即官方 layer_id=0，该层不做 value residual（v_first = v），故不含 v0/v1/v2，
      不把不参与前向的死参数计入预算。
    """
    if backbone == "mlp":
        h = HID
        return 2 * h * h + (D + 3) * h + 2
    if backbone == "gru":
        h = GRU_HID
        return 5 * h * h + (3 * D + 8) * h + 2
    if backbone == "transformer":
        d, ff = TR_D, TR_FF
        return 6 * d * d + 2 * d * ff + ff + (D + 12) * d + 2
    if backbone == "cnn":
        c, k, n = CNN_C, CNN_K, CNN_LAYERS
        return (k * (n - 1) + 2) * c * c + (k * D + n + 2) * c + 2
    if backbone == "rwkv7":
        c, r = RWKV_C, RWKV_LORA
        return 6 * c * c + 6 * c * r + (D + 16) * c + 2
    raise ValueError(f"未知骨干：{backbone}")


def hid_of(backbone):
    return {"mlp": HID, "gru": GRU_HID, "transformer": TR_D,
            "cnn": CNN_C, "rwkv7": RWKV_C}[backbone]


def rwkv7_op(r, w, k, v, a, b, head):
    """RWKV-7 状态递归，官方纯 PyTorch 参考路径。

    逐字照 BlinkDL/RWKV-LM 固定提交 952102498e9ed367ea0a59ee64106916d474d30f 的
    RWKV-v7/rwkv_v7_demo.py 第 168-200 行（RWKV7_OP 在 USE_CUDA_KERNEL=False 时的分支），
    只把文件级常量 HEAD_SIZE 改为入参 head，并去掉末尾向 DTYPE 的回转（本脚本全程 fp32）。
    未使用官方 CUDA 内核 wkv7.cu / wkv7_cuda_fp32.cu。
    """
    B, T, C = r.size()
    H = C // head
    N = head
    r = r.view(B, T, H, N).float()
    k = k.view(B, T, H, N).float()
    v = v.view(B, T, H, N).float()
    a = a.view(B, T, H, N).float()
    b = b.view(B, T, H, N).float()
    w = torch.exp(-torch.exp(w.view(B, T, H, N).float()))
    out = torch.zeros((B, T, H, N), device=r.device, dtype=torch.float)
    state = torch.zeros((B, H, N, N), device=r.device, dtype=torch.float)

    for t in range(T):
        kk = k[:, t, :].view(B, H, 1, N)
        rr = r[:, t, :].view(B, H, N, 1)
        vv = v[:, t, :].view(B, H, N, 1)
        aa = a[:, t, :].view(B, H, N, 1)
        bb = b[:, t, :].view(B, H, 1, N)
        state = state * w[:, t, :, None, :] + state @ aa @ bb + vv @ kk
        out[:, t, :] = (state @ rr).view(B, H, N)

    return out.view(B, T, C)


class RWKV7TimeMix(nn.Module):
    """RWKV-7 单个时间混合块，以官方源码为参照实现。

    参照：BlinkDL/RWKV-LM，提交 952102498e9ed367ea0a59ee64106916d474d30f，Apache-2.0。
      结构与前向：RWKV-v7/rwkv_v7_demo.py 第 209-289 行 class RWKV_Tmix_x070。
      初始化常数：RWKV-v7/train_temp/rwkv7_train_simplified.py 第 66-146 行同名类
                  （x_* 的幂次、w0 的 www/zigzag、a0、k_k、k_a、r_k、四个线性层的均匀初始化尺度、
                    ortho_init 与 D_*_LORA=8 的小模型取值）。
      状态递归：rwkv_v7_demo.py 第 168-200 行的纯 PyTorch 参考路径（非 CUDA 内核）。
    单块对应官方 layer_id=0：ratio_0_to_1 = 0/(n_layer-1) = 0，ratio_1_to_almost0 = 1 - 0/n_layer = 1，
    且该层 v_first = v、不做 value residual，故不含 v0/v1/v2。
    """

    def __init__(self, c=RWKV_C, head=RWKV_HEAD, lora=RWKV_LORA):
        super().__init__()
        C, N = c, head
        assert C % N == 0, f"RWKV-7 通道 {C} 必须能被 head_size {N} 整除"
        H = C // N
        self.C, self.N, self.H = C, N, H
        with torch.no_grad():
            ratio_0_to_1 = 0.0            # layer_id / (n_layer - 1)，单块即 layer_id=0
            ratio_1_to_almost0 = 1.0      # 1 - layer_id / n_layer，单块即 layer_id=0
            ddd = torch.ones(1, 1, C)
            for i in range(C):
                ddd[0, 0, i] = i / C
            self.x_r = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))
            self.x_w = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_k = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_v = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_a = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_g = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))

            def ortho_init(x, scale):
                with torch.no_grad():
                    shape = x.shape
                    if len(shape) == 2:
                        gain = math.sqrt(shape[0] / shape[1]) if shape[0] > shape[1] else 1
                        nn.init.orthogonal_(x, gain=gain * scale)
                    elif len(shape) == 3:
                        gain = math.sqrt(shape[1] / shape[2]) if shape[1] > shape[2] else 1
                        for i in range(shape[0]):
                            nn.init.orthogonal_(x[i], gain=gain * scale)
                    else:
                        assert False
                    return x

            www = torch.zeros(C)
            zigzag = torch.zeros(C)
            linear = torch.zeros(C)
            for n in range(C):
                linear[n] = n / (C - 1) - 0.5
                zigzag[n] = ((n % N) - ((N - 1) / 2)) / ((N - 1) / 2)
                zigzag[n] = zigzag[n] * abs(zigzag[n])
                www[n] = -6 + 6 * (n / (C - 1)) ** (1 + 1 * ratio_0_to_1 ** 0.3)

            self.w1 = nn.Parameter(torch.zeros(C, lora))
            self.w2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))
            self.w0 = nn.Parameter(www.reshape(1, 1, C) + 0.5 + zigzag * 2.5)

            self.a1 = nn.Parameter(torch.zeros(C, lora))
            self.a2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))
            self.a0 = nn.Parameter(torch.zeros(1, 1, C) - 0.19 + zigzag * 0.3 + linear * 0.4)

            self.g1 = nn.Parameter(torch.zeros(C, lora))
            self.g2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))

            self.k_k = nn.Parameter(torch.zeros(1, 1, C) + 0.71 - linear * 0.1)
            self.k_a = nn.Parameter(torch.zeros(1, 1, C) + 1.02)
            self.r_k = nn.Parameter(torch.zeros(H, N) - 0.04)

            self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))
            self.receptance = nn.Linear(C, C, bias=False)
            self.key = nn.Linear(C, C, bias=False)
            self.value = nn.Linear(C, C, bias=False)
            self.output = nn.Linear(C, C, bias=False)
            self.ln_x = nn.GroupNorm(H, C, eps=64e-5)

            self.receptance.weight.data.uniform_(-0.5 / (C ** 0.5), 0.5 / (C ** 0.5))
            self.key.weight.data.uniform_(-0.05 / (C ** 0.5), 0.05 / (C ** 0.5))
            self.value.weight.data.uniform_(-0.5 / (C ** 0.5), 0.5 / (C ** 0.5))
            self.output.weight.data.zero_()

    def forward(self, x):
        B, T, C = x.size()
        H = self.H
        xx = self.time_shift(x) - x

        xr = x + xx * self.x_r
        xw = x + xx * self.x_w
        xk = x + xx * self.x_k
        xv = x + xx * self.x_v
        xa = x + xx * self.x_a
        xg = x + xx * self.x_g

        r = self.receptance(xr)
        w = -F.softplus(-(self.w0 + torch.tanh(xw @ self.w1) @ self.w2)) - 0.5   # 软钳到 (-inf, -0.5)
        k = self.key(xk)
        v = self.value(xv)                       # 单块即 layer_id=0：v_first = v，无 value residual
        a = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)                    # 上下文内学习率
        g = torch.sigmoid(xg @ self.g1) @ self.g2

        kk = k * self.k_k
        kk = F.normalize(kk.view(B, T, H, -1), dim=-1, p=2.0).view(B, T, C)
        k = k * (1 + (a - 1) * self.k_a)

        y = rwkv7_op(r, w, k, v, -kk, kk * a, self.N)
        y = self.ln_x(y.view(B * T, C)).view(B, T, C)
        y = y + ((r.view(B, T, H, -1) * k.view(B, T, H, -1) * self.r_k).sum(dim=-1, keepdim=True)
                 * v.view(B, T, H, -1)).view(B, T, C)
        y = self.output(y * g)
        return y


class Model(nn.Module):
    """结构与 ch3_full.Model 相同；只有逐流编码器 encode() 随 backbone 切换。

    五个骨干共用同一组合头 g、同一输出头 o 与同一 p_log，因果前缀均值 c 与
    Lp 池化、辅助损失、评价口径一律不动。
    """

    def __init__(self, backbone, agg, lp, hid=None, dp=0.1):
        super().__init__(); self.agg, self.lp = agg, lp
        self.backbone = backbone
        hid = hid_of(backbone) if hid is None else hid
        if backbone == "mlp":
            self.f = nn.Sequential(nn.Linear(D, hid), nn.ReLU(), nn.Dropout(dp))
        elif backbone == "gru":
            self.f = nn.GRU(input_size=D, hidden_size=hid, num_layers=1, bias=True,
                            batch_first=True, bidirectional=False)
        elif backbone == "transformer":
            self.inp = nn.Linear(D, hid)
            self.att = nn.MultiheadAttention(embed_dim=hid, num_heads=TR_HEADS,
                                             dropout=dp, batch_first=True)
            self.n1 = nn.LayerNorm(hid); self.n2 = nn.LayerNorm(hid)
            self.ff = nn.Sequential(nn.Linear(hid, TR_FF), nn.ReLU(), nn.Dropout(dp),
                                    nn.Linear(TR_FF, hid))
        elif backbone == "cnn":
            self.conv = nn.ModuleList(
                [nn.Conv1d(D if i == 0 else hid, hid, CNN_K) for i in range(CNN_LAYERS)])
            self.act = nn.ReLU(); self.drop = nn.Dropout(dp)
        elif backbone == "rwkv7":
            self.inp = nn.Linear(D, hid)
            self.tmix = RWKV7TimeMix(hid, RWKV_HEAD, RWKV_LORA)
        else:
            raise ValueError(f"未知骨干：{backbone}")
        self.hid = hid
        self.g = nn.Sequential(nn.Linear(hid * 2, hid), nn.ReLU(), nn.Dropout(dp))
        self.o = nn.Linear(hid, 1); self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def encode(self, x, m):
        """逐流编码器。输出恒为掩码后的 (B, L, hid)，补零位严格为 0，且位置 t 只依赖 <= t。"""
        if self.backbone == "mlp":
            return self.f(x) * m.unsqueeze(-1)
        if self.backbone == "gru":
            # lengths 必须在 CPU 上；enforce_sorted=False 由 PyTorch 内部排序再还原顺序
            lens = m.sum(1).to(torch.int64).clamp(min=1).cpu()
            packed = pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
            out, _ = self.f(packed)
            h, _ = pad_packed_sequence(out, batch_first=True, total_length=x.shape[1])
            return h * m.unsqueeze(-1)
        if self.backbone == "cnn":
            # 因果一维卷积：只在左侧补 k-1 个零，位置 t 的感受野落在 [t-(k-1), t]
            h = (x * m.unsqueeze(-1)).transpose(1, 2)
            for conv in self.conv:
                h = self.drop(self.act(conv(F.pad(h, (CNN_K - 1, 0)))))
            return h.transpose(1, 2) * m.unsqueeze(-1)
        if self.backbone == "rwkv7":
            h0 = self.inp(x * m.unsqueeze(-1)) * m.unsqueeze(-1)
            return self.tmix(h0) * m.unsqueeze(-1)
        # transformer：单层因果掩码自注意力编码器块
        n = x.shape[1]
        mv = m.unsqueeze(-1) > 0.5
        h0 = self.inp(x) * m.unsqueeze(-1)
        cm = torch.triu(torch.full((n, n), float("-inf"), device=x.device, dtype=h0.dtype),
                        diagonal=1)                                   # 位置 t 只能看 <= t
        a, _ = self.att(h0, h0, h0, attn_mask=cm, key_padding_mask=(m < 0.5),
                        need_weights=False)
        a = torch.where(mv, a, torch.zeros_like(a))                   # 全掩码行不产生 NaN
        z = self.n1(h0 + a)
        h = self.n2(z + self.ff(z))
        return h * m.unsqueeze(-1)

    def forward(self, x, m):
        h = self.encode(x, m)
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


# =====================================================================================
# 实现验证（合成数据，真值由构造给定；不创建运行身份、不产生任何指标、不进结果表）
#   性质一 掩码决定性：补零位输入换成 1e3 噪声，真实位输出必须逐位不变，且补零位输出恒为 0
#   性质二 因果性    ：改动位置 > t 的输入，位置 <= t 的输出必须不变（四个新骨干逐一验）
#   性质三 参数量解析公式与 torch 实测一致
# 判据一律 <1e-6；超阈先做 TF32 归因诊断，不放宽阈值，也不改训练与评价的默认精度设置。
# =====================================================================================
def _impl_verify():
    log("=" * 96)
    log("实现验证（合成数据，真值由构造给定；只报通过/不通过，不进结果表）")
    rep = {}
    for bk in ["mlp"] + BACKBONES:
        want = npar_formula(bk)
        got = sum(p.numel() for p in Model(bk, True, True).parameters())
        assert got == want, f"{bk} 参数量公式 {want} 与 torch 实测 {got} 不一致"
        rep[f"npar_{bk}"] = got
        log(f"  参数量 {bk:<11} 公式={want:,} torch实测={got:,} 一致 | "
            f"相对 MLP {100.0*(got-MLP_NPAR)/MLP_NPAR:+.3f}%")

    torch.manual_seed(SEED)
    b = 8
    xs = torch.randn(b, L, D, device=dev)
    lens = torch.tensor([1, 3, 17, 64, 96, 127, 128, 128], device=dev)
    ms = (torch.arange(L, device=dev).unsqueeze(0) < lens.unsqueeze(1)).to(xs.dtype)
    pad = (ms < 0.5).unsqueeze(-1)
    T_PROBE = [0, 1, 5, 31, 63, 100, 126]

    def _causal_worst(net, tf32):
        _mm, _cd = torch.backends.cuda.matmul.allow_tf32, torch.backends.cudnn.allow_tf32
        torch.backends.cuda.matmul.allow_tf32 = tf32
        torch.backends.cudnn.allow_tf32 = tf32
        w = 0.0
        with torch.no_grad():
            base = net.encode(xs, ms)
            for t in T_PROBE:
                xt = xs.clone()
                xt[:, t + 1:, :] = torch.randn_like(xt[:, t + 1:, :]) * 1e3
                ht = net.encode(xt, ms)
                w = max(w, (ht[:, :t + 1] - base[:, :t + 1]).abs().max().item())
        torch.backends.cuda.matmul.allow_tf32 = _mm
        torch.backends.cudnn.allow_tf32 = _cd
        return w

    for bk in BACKBONES:
        net = Model(bk, True, True).to(dev).eval()
        with torch.no_grad():
            h0 = net.encode(xs, ms)
            x2 = torch.where(pad, torch.randn_like(xs) * 1e3, xs)
            h1 = net.encode(x2, ms)
            d_mask = (h1 - h0).abs().max().item()
            d_pad = h0.masked_select(pad.expand_as(h0)).abs().max().item()
        rep[f"{bk}_mask_determinism_maxabs"] = d_mask
        rep[f"{bk}_pad_output_maxabs"] = d_pad
        log(f"  性质一 {bk:<11} 掩码决定性：补零位改 1e3 噪声后真实位最大差={d_mask:.3e}（判据 <1e-6）"
            f"；补零位输出最大绝对值={d_pad:.3e}（判据 =0）")
        assert d_mask < 1e-6, f"{bk} 掩码决定性不通过：{d_mask:.3e}"
        assert d_pad == 0.0, f"{bk} 补零位输出非零：{d_pad:.3e}"

        worst = _causal_worst(net, torch.backends.cuda.matmul.allow_tf32)
        rep[f"{bk}_causality_maxabs"] = worst
        log(f"  性质二 {bk:<11} 因果性：改动位置>t 后位置<=t 最大差={worst:.3e}（判据 <1e-6）")
        if worst >= 1e-6:
            log("         超阈，先做归因诊断：关闭 TF32 重测（不改变训练与评价的默认精度设置）")
            w2 = _causal_worst(net, False)
            rep[f"{bk}_causality_maxabs_tf32_off"] = w2
            log(f"         TF32 关闭后最大差={w2:.3e}")
        assert worst < 1e-6, f"{bk} 因果性不通过：{worst:.3e}"
        del net
        torch.cuda.empty_cache()

    json.dump(rep, open(f"{OUT}/impl_verification.json", "w"), ensure_ascii=False, indent=2)
    log(f"  实现验证全部通过，收据 {OUT}/impl_verification.json")
    return rep


IMPL = _impl_verify()


def train_and_select(backbone, agg, lp, seed, tag):
    """训练 20 epoch 不早停，逐 epoch 用 LSPR23 验证 AP 选检查点。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(backbone, agg, lp).to(dev)
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
log(f"四骨干 × 四格 seed={SEED}，{N_EPOCH} epoch × {EPOCH_STEPS} 步 = {N_EPOCH*EPOCH_STEPS} 步，不早停，串行训练")
for bk in BACKBONES:
    log(f"########## 骨干 {bk}（隐藏维 {hid_of(bk)}，参数 {npar_formula(bk):,}）##########")
    for cid, agg, lp in CELLS:
        key = f"{bk}-{cid}"
        log(f"--- {key} (agg={agg}, lp={lp}) ---")
        best, hist, tr_t, npar = train_and_select(bk, agg, lp, SEED, key)
        assert npar == npar_formula(bk), f"{key} 参数量 {npar} 与公式 {npar_formula(bk)} 不一致"
        SEL[key] = {"backbone": bk, "cell": cid, "agg": agg, "lp": lp,
                    "best": best, "hist": hist, "tr": tr_t, "npar": npar}

# =====================================================================================
# 阶段闸门：先把选择结果写盘冻结，再允许读入 LSPR24
# =====================================================================================
_frozen = {"protocol": "逐epoch在LSPR23实体不相交验证集上取逐流AP最大的epoch，无末5平均，不早停",
           "run_id": RUN_ID, "backbones": BACKBONES,
           "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "cells": {c: {"backbone": SEL[c]["backbone"], "cell_id": SEL[c]["cell"],
                         "selected_epoch": SEL[c]["best"]["epoch"],
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
# 数据身份：X24 与上面的 X23 同源，是标准化后的特征矩阵，不是 raw83 原值。见缓存目录 README.md。
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
for bk in BACKBONES:
    for cid, agg, lp in CELLS:
        key = f"{bk}-{cid}"
        net = Model(bk, agg, lp).to(dev)
        net.load_state_dict(SEL[key]["best"]["state"])
        p = net.p.item()
        assert abs(p - SEL[key]["best"]["p"]) < 1e-9, f"{key} 权重回载后 p 不一致"
        t1 = time.time()
        sc, seen = score24(net)
        ev_t = time.time() - t1
        fap = average_precision_score(y24[seen], sc[seen])
        fauc = roc_auc_score(y24[seen], sc[seen])
        e_max, n_ent_ok = ent_ap(sc, seen)
        e_lp, _ = ent_ap(sc, seen, p if lp else None)     # ch3_full 口径：lp=False 时退化为 max
        dr_main = dr_at_fpr(sc, seen, 0.04, p if lp else None)
        dr_max = dr_at_fpr(sc, seen, 0.04, None)
        RES[key] = {"backbone": bk, "cell": cid, "agg": agg, "lp": lp,
                    "sel_epoch": SEL[key]["best"]["epoch"],
                    "val_ap": SEL[key]["best"]["ap"], "p": p,
                    "fap": float(fap), "fauc": float(fauc),
                    "e_max": float(e_max), "e_lp": float(e_lp),
                    "dr_main": float(dr_main), "dr_max": float(dr_max),
                    "n_ent_scored": int(n_ent_ok), "tr": SEL[key]["tr"], "ev": ev_t,
                    "npar": SEL[key]["npar"]}
        log(f"{key}: epoch={SEL[key]['best']['epoch']:>2} 验证AP={SEL[key]['best']['ap']:.6f} p={p:.4f} | "
            f"逐流AP={fap:.6f} AUC={fauc:.6f} 实体AP(max)={e_max:.6f} 实体AP(Lp)={e_lp:.6f} "
            f"DR@4%FPR={dr_main:.6f} (max口径={dr_max:.6f}) 覆盖实体={n_ent_ok:,} "
            f"训练{SEL[key]['tr']/60:.2f}分 推理{ev_t:.1f}秒")
        if cid == "C11":
            np.save(f"{OUT}/scores_{bk}_C11.npy", sc); np.save(f"{OUT}/seen_{bk}_C11.npy", seen)
            log(f"  {bk} C11 逐流分数已存 {OUT}/scores_{bk}_C11.npy")
        del sc, seen, net
        torch.cuda.empty_cache()

_N_EXPECT = len(BACKBONES) * len(CELLS)
assert _EVAL24_CALLS == _N_EXPECT, f"LSPR24 评价次数应为 {_N_EXPECT}（每格一次），实为 {_EVAL24_CALLS}"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次（每格恰一次），均发生在选择冻结之后")

# =====================================================================================
# 交互项与组合创新判据（逐骨干各算一次）
# =====================================================================================
INTER = {}
log("=" * 96)
log("2x2 交互项：交互 = C11 − C10 − C01 + C00；组合创新 = 交互>0 且 组合>单模块之和")
for bk in BACKBONES:
    for label, key in [("实体AP(主口径: lp格用Lp, 非lp格用max)", "e_lp"),
                       ("实体AP(全格 max 口径)", "e_max"),
                       ("DR@4%FPR(主口径)", "dr_main"),
                       ("DR@4%FPR(全格 max 口径)", "dr_max"),
                       ("逐流AP", "fap")]:
        v = {c: RES[f"{bk}-{c}"][key] for c in ["C00", "C01", "C10", "C11"]}
        eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
        inter = eAB - (eA + eB)
        c1 = inter > 0; c2 = eAB > (eA + eB); c3 = eAB > 0
        INTER[f"{bk}-{key}"] = {"backbone": bk, "label": label,
                                "C00": v["C00"], "C01": v["C01"], "C10": v["C10"], "C11": v["C11"],
                                "A": eA, "B": eB, "sum": eA + eB, "combo": eAB, "interaction": inter,
                                "crit_interaction_pos": bool(c1), "crit_combo_gt_sum": bool(c2),
                                "crit_combo_pos": bool(c3), "combo_innovation": bool(c1 and c3)}
        log(f"\n【{bk} | {label}】")
        log(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}")
        log(f"  A(仅聚合)={eA:+.6f}  B(仅Lp)={eB:+.6f}  之和={eA+eB:+.6f}  组合={eAB:+.6f}  交互={inter:+.6f}")
        log(f"  判据一 交互>0: {'通过' if c1 else '不通过'} | 判据二 组合>基线: {'通过' if c3 else '不通过'}"
            f" | ★ 组合创新{'成立' if (c1 and c3) else '不成立'}")

# ---- 与 MLP 骨干（同为协议 A）的逐格对比：数字取自冻结制品 ch3_2x2_fairsel_results.json ----
assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入含 LSPR24 指标的 MLP 参照"
_mref = json.load(open(MLP_REF))
assert _mref["seed"] == SEED and _mref["isolation"]["lspr24_evals"] == 4, "MLP 参照制品身份不符"
MLP_A = {c: {k: _mref["cells"][c][k] for k in
             ["sel_epoch", "val_ap", "p", "fap", "fauc", "e_max", "e_lp", "dr_main", "dr_max",
              "npar", "tr", "ev"]}
         for c in ["C00", "C01", "C10", "C11"]}
_EXP_MLP_ELP = {"C00": 0.334994, "C01": 0.408513, "C10": 0.385970, "C11": 0.518350}
for c, want in _EXP_MLP_ELP.items():
    got = MLP_A[c]["e_lp"]
    assert abs(got - want) < 5e-7, f"MLP 参照 {c} 实体AP(主口径) 应为 {want}，实为 {got:.6f}"
    assert MLP_A[c]["npar"] == MLP_NPAR, f"MLP 参照 {c} 参数量应为 {MLP_NPAR}"
log("=" * 96)
log("MLP 参照自检通过（协议 A 冻结数字）：C00 0.334994 / C01 0.408513 / C10 0.385970 / C11 0.518350")
for bk in BACKBONES:
    log(f"--- 骨干 {bk} 相对 MLP 骨干（同协议 A）的逐格差 ---")
    for cid in ["C00", "C01", "C10", "C11"]:
        r = RES[f"{bk}-{cid}"]; m = MLP_A[cid]
        log(f"  {cid}: 逐流AP {m['fap']:.6f}→{r['fap']:.6f} ({r['fap']-m['fap']:+.6f}) | "
            f"实体AP(主) {m['e_lp']:.6f}→{r['e_lp']:.6f} ({r['e_lp']-m['e_lp']:+.6f}) | "
            f"实体AP(max) {m['e_max']:.6f}→{r['e_max']:.6f} ({r['e_max']-m['e_max']:+.6f}) | "
            f"DR@4%FPR {m['dr_main']:.6f}→{r['dr_main']:.6f} ({r['dr_main']-m['dr_main']:+.6f})")
    d = RES[f"{bk}-C11"]["e_lp"] - RES[f"{bk}-C00"]["e_lp"]
    dm = MLP_A["C11"]["e_lp"] - MLP_A["C00"]["e_lp"]
    log(f"  C11−C00 实体AP(主口径) 增益：{bk} {d:+.6f}（{d*100:+.2f} 点） vs MLP {dm:+.6f}（{dm*100:+.2f} 点）")

# ---- 与 XGBoost 实体基线对比 ----
XGB = {"e_lp": 0.531917, "dr_main": 0.816489, "fap": 0.222391}
log("=" * 96)
log("与 XGBoost 实体基线对比（XGB: 实体AP(Lp)=0.531917 DR@4%FPR=0.816489 逐流AP=0.222391）")
for bk in BACKBONES:
    for cid in ["C00", "C01", "C10", "C11"]:
        r = RES[f"{bk}-{cid}"]
        log(f"  {bk}-{cid}: 实体AP {r['e_lp']:.6f} ({r['e_lp']-XGB['e_lp']:+.6f}) | "
            f"DR@4%FPR {r['dr_main']:.6f} ({r['dr_main']-XGB['dr_main']:+.6f}) | "
            f"逐流AP {r['fap']:.6f} ({r['fap']-XGB['fap']:+.6f})")

json.dump({"protocol": _frozen["protocol"], "run_id": RUN_ID, "seed": SEED,
           "backbones": {bk: {"hid": hid_of(bk), "npar": npar_formula(bk),
                              "npar_rel_mlp": (npar_formula(bk) - MLP_NPAR) / MLP_NPAR}
                         for bk in ["mlp"] + BACKBONES},
           "transformer_config": {"d_model": TR_D, "num_heads": TR_HEADS,
                                  "head_dim": TR_D // TR_HEADS, "ffn_dim": TR_FF},
           "gru_config": {"hidden": GRU_HID, "num_layers": 1, "bidirectional": False},
           "cnn_config": {"channels": CNN_C, "kernel": CNN_K, "layers": CNN_LAYERS,
                          "causal_left_pad": CNN_K - 1,
                          "receptive_field": CNN_LAYERS * (CNN_K - 1) + 1},
           "rwkv7_config": {"channels": RWKV_C, "head_size": RWKV_HEAD,
                            "n_head": RWKV_C // RWKV_HEAD, "lora_dim": RWKV_LORA,
                            "source_repo": "https://github.com/BlinkDL/RWKV-LM",
                            "source_commit": "952102498e9ed367ea0a59ee64106916d474d30f",
                            "source_license": "Apache-2.0",
                            "structure_ref": "RWKV-v7/rwkv_v7_demo.py 第209-289行 RWKV_Tmix_x070",
                            "init_ref": "RWKV-v7/train_temp/rwkv7_train_simplified.py 第66-146行",
                            "recurrence_ref": "RWKV-v7/rwkv_v7_demo.py 第168-200行 纯PyTorch参考路径",
                            "cuda_kernel_used": False},
           "impl_verification": IMPL,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                      "flow_pos_rate": _flow_pos, "entity_prior": float(ent_lab.mean())},
           "cells": RES, "selection": _frozen["cells"], "interaction": INTER,
           "mlp_protocolA_reference": MLP_A, "xgb_reference": XGB,
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS}},
          open(f"{OUT}/ch3_backbone_protocolA_results.json", "w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_backbone_protocolA_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
