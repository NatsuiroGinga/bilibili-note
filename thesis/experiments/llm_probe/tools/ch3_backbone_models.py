# -*- coding: utf-8 -*-
"""第三章基座骨干共享定义：从 tools/ch3_backbone_protocolA_v2.py 抽取，供协议 A/B 等多个入口 import 复用。

本文件是纯定义模块，不含任何脚本级副作用：无 argparse、无数据加载、无训练循环、
无 GPU 上卡、无日志打印。import 本文件不产生任何可观测行为。

背景：`ch3_backbone_protocolA_v2.py` 是已产出正式历史结果的冻结协议脚本（v1→v2 只增加
持久化与运行编排，训练/选择/评价语义逐字保持不变），其结构是"从上到下线性执行的脚本"
（顶层 `argparse.parse_args()` 立即读取 `--backbone` 等必填参数、随后立即 `np.load` 大文件），
因此不能被安全 `import`。2026-08-27 协议 B 骨干消融重跑（服务器正式重跑合同）要求"复用其
模型类（Model、encode 分支）...禁止复制粘贴重写模型，用 import 或最小改造"，故做此次抽取：
把与数据加载无关的纯定义（五个骨干的参数量公式、隐藏维超参、lp_pool、RWKV-7 状态递归与
官方对齐实现、Model 类结构与 encode() 分支、LSPR23 实体不相交切分公式）搬到本文件，
`ch3_backbone_protocolA_v2.py` 相应位置改为从本文件 import，其余训练/选择/评价/持久化/
运行编排代码逐字不变。

下列内容与 `ch3_backbone_protocolA_v2.py` 原实现完全等价（只是换了文件位置，未改一行逻辑）：
  - 五个骨干（mlp/gru/transformer/cnn/rwkv7）的隐藏维超参与参数量解析公式
  - `lp_pool`：Lp 池化聚合
  - `rwkv7_op` / `RWKV7TimeMix`：RWKV-7 单块状态递归，逐字对齐官方仓库
    BlinkDL/RWKV-LM 固定提交 952102498e9ed367ea0a59ee64106916d474d30f
    （结构与前向见 RWKV-v7/rwkv_v7_demo.py 第209-289行 class RWKV_Tmix_x070；
     初始化常数见 RWKV-v7/train_temp/rwkv7_train_simplified.py 第66-146行同名类；
     状态递归见 rwkv_v7_demo.py 第168-200行纯 PyTorch 参考路径），Apache-2.0 许可证。
  - `Model`：五个骨干共用同一组合头 g、同一输出头 o、同一 p_log，因果前缀均值聚合与
    Lp 池化、encode() 逐流编码器分支不动。
  - `split_lspr23_entity_disjoint`：LSPR23 实体不相交验证划分，逐字照抄
    `select_signal.py` 第151-168行（本任务只用"实体不相交"一种）。

D 在 `ch3_backbone_protocolA_v2.py` 原文中由 `D = X23.shape[1]` 运行时赋值，
本文件把它写成硬编码常量 83（该断言已在多处数据自检中反复核验：Dijk 2026 附录 A 口径）；
调用方仍应在加载 X23 后自行 `assert X23.shape[1] == D` 做数据完整性核验。
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

# ---- 特征数：Dijk 2026 附录 A 口径，多处数据自检已反复核验 ----
D = 83

# ---- 骨干隐藏维（唯一新增的超参，只为对齐 MLP 的 90,242 参数预算）----
MLP_NPAR = 90242
HID = 192                         # mlp 骨干隐藏维；逐字照抄 ch3_full.py 第 52、106-107 行
GRU_HID = 111                     # 5h² + (3D+8)h + 2 = 90,134，偏 -0.120%
TR_D, TR_HEADS = 77, 7            # 6d² + 2·d·ff + ff + (D+12)d + 2 = 90,631，偏 +0.431%；head_dim = 11
TR_FF = 4 * TR_D                  # 标准 4× 前馈宽度 = 308
CNN_C, CNN_K, CNN_LAYERS = 92, 3, 3   # (2k+2)c² + (kD+5)c + 2 = 91,082，偏 +0.931%
RWKV_C, RWKV_HEAD, RWKV_LORA = 112, 16, 8   # 6C² + 6·C·lora + (D+16)C + 2 = 91,730，偏 +1.649%
ALL_BACKBONES = ["gru", "transformer", "cnn", "rwkv7"]


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


def split_lspr23_entity_disjoint(E23, T23, seed, val_frac, time_tail):
    """LSPR23 实体不相交验证划分。逐字照抄 select_signal.py 第 151-168 行（只用"实体不相交"）。

    返回 (tr_idx, val_idx)：训练区排除验证实体与时间尾部，验证集只取验证实体且排除时间尾部。
    调用方须自行核验切分统计（本函数不做数据集特定的计数断言，那些断言属于调用方的数据完整性核验）。
    """
    rs = np.random.RandomState(seed)
    uent = np.unique(E23)
    perm = rs.permutation(len(uent))
    val_ent = set(uent[perm[:max(1, int(len(uent) * val_frac))]].tolist())
    m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
    t_cut = np.quantile(T23, 1.0 - time_tail)
    m_time = T23 >= t_cut                                                 # 时间尾部（本任务不用作信号）
    tr_mask = ~(m_ent | m_time)                                           # 训练区：两者都排除
    tr_idx = np.flatnonzero(tr_mask)
    val_idx = np.flatnonzero(m_ent & ~m_time)                             # 唯一选择信号的来源
    assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
    return tr_idx, val_idx


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
