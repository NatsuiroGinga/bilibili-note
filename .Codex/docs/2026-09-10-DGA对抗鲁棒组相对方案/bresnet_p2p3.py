#!/usr/bin/env python3
"""B-ResNet（第二骨干）P2/P3 四臂：A（干净）／D（组相对过滤 top-64）／F（D＋良性误报加权 3.0）／G（只良性加权）。

许可证边界（强制，2026-09-11）
--------------------------------------------------------------------------
B-ResNet 官方实现 `https://gitlab.com/rwth-itsec/robust-dga-detection`
（commit `599e8a92460f7c56137c7333a3010af2a67522d2`，2024-06-29）为 **AGPL-3.0**
（`thesis/methods/第三章-方法来源台账.md` §五）。本文件**未复制该仓库任何代码**，
模型与编码器只按已登记规格表重写；来源：

- `thesis/methods/第三章-方法来源台账.md` §五（骨干表：URL／commit／许可证／字符表 40 项／参数量登记 155,009）
- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/zhuh-ch3-benchmark.md` §7.2（架构规格表）
- `wiki/papers/attack-detection/dga/2020-Drichel-DGA分类器真实适用性.md`（论文原文规格）
- 臂框架复用 `official_p2p3.py`（**本仓库自有代码**，非 AGPL 来源）：`perturb2`／`perturb_half`
  与数据切分装载按 import 复用，保证对抗变体字符串与 DRIFT 侧逐字一致。

论文未明示的项一律在注释标「论文未明示，任务化设定」。

架构规格（逐项对应 §7.2 表）
--------------------------------------------------------------------------
| 项 | 规格（§7.2） | 本文件实现 |
| --- | --- | --- |
| 输入视图 | `[B, SEQ_LEN, 128] → permute → [B, 128, SEQ_LEN]` | `BResNet.forward` |
| 嵌入 | `nn.Embedding(num_embeddings=40, embedding_dim=128)` | `self.embedding` |
| 残差块数 | **1**（论文 §3.2 正文 *"we use a single residual block"* ＋官方代码；图 1(a)「6 Residuals」为已登记矛盾项，**不采用**） | `n_blocks=1` |
| 块内 | `Conv1d(k=4, s=1, padding='same') → ReLU → Conv1d(k=4, s=1, padding='same') → 与输入相加` | `ResidualITsec.forward` |
| 通道对齐 | 仅当 `in≠out` 时用 1×1 `channel_adjust`；本配置 `128=128` ⇒ **本配置下不生效** | 模块常驻、前向按条件使用（见「遗留风险」） |
| 块后 | `F.relu` → `F.max_pool1d(kernel_size=4, padding=2)` | 同 |
| 展平 | `128 × ceil(63/4) = 128 × 16 = 2048` | `h.reshape(B, -1)` |
| 输出 | `nn.Linear(2048, 1)`，**默认返回 logits** | `self.classifier` |
| 损失／优化 | BCE ＋ Adam，batch `128`（论文 §3.2，p.3） | `binary_cross_entropy_with_logits` ＋ `Adam` |
| `seq_len` | **63（e2LD）**——官方代码默认，docstring *"Use 63 for e2LDs"* | `SEQ_LEN = 63` |

与 DRIFT 侧的口径差异（**登记，不隐藏**）
--------------------------------------------------------------------------
1. **单分支 logits，无 `classifier_head` 双支融合**：`official_p2p3.py` 走
   `diag.branch_features` ＋ `diag.probabilities(..., tok_mean, char_mean, ...)`——
   即「字符支／子词支分别中和到训练集均值后再融合」。B-ResNet 无该双支结构，
   **不使用 `diag.probabilities`，也不做中和均值**；`p_mal = sigmoid(logit)`。
   两个口径都是「模型输出的恶意概率」，但**中和均值是 DRIFT 专有的结构适配**，
   本臂不存在该步骤。
2. **损失等价性**：`F.binary_cross_entropy_with_logits(z, y)` 与
   `F.cross_entropy([0, z], y)` 对两类逐样本取值相同（`y=1 → softplus(z)`，
   `y=0 → softplus(−z)`），故 `(ce·w).sum()/n_tot` 的函数形式与 DRIFT 侧逐位同构。
3. **不分层 lr**：官方 DRIFT 权重是预训练模型，用分层 lr（骨干 1e-6／头 1e-4）；
   B-ResNet 为 155K 参数从头训练，**无预训练分层需求**，按简报冻结为**全参数单 lr `1e-3`**。

数值登记（根 `AGENTS.md` 魔法数字门禁）
--------------------------------------------------------------------------
| 数值 | 用途 | 依据 | 核验状态 |
| --- | --- | --- | --- |
| `128` | 训练批量 | 论文 §3.2 p.3 明确给出；与 `official_p2p3.py` 同值 | 已核验（原文） |
| `63` | 序列长度 | 官方代码默认且注明用于 e2LD（§7.2 表）；简报冻结 | 已核验（规格表） |
| `3` | 训练轮数 | 论文未给、官方仓库无训练脚本 ⇒ 沿用 p2p3 冻结规格 | 任务化设定（继承冻结，**无直接文献依据**） |
| `42` | 随机种子 | 同上 | 任务化设定（继承冻结） |
| `0.5` | 判正阈值 | 同上 | 任务化设定（继承冻结） |
| `40` | 词表大小 | §7.2 表 `nn.Embedding(40, 128)` | 已核验（规格表） |
| `1e-3` | 全参数学习率 | **无直接文献依据**：论文只给「Adam」，官方仓库无训练脚本；分层 lr 面向预训练权重，本模型从头训练**无对应物** | 任务化设定（简报冻结，**未验证**） |
| `0` | Adam 权衰减 | **无直接文献依据**（论文未给）；沿用 `torch.optim.Adam` 默认 | 任务化设定 |
| `3.0` | 组件 2 良性误报权重 | 沿用 p2p3 冻结值（该值本身无文献精确值） | 任务化设定（继承冻结） |
| `64` | 组件 1 跨组配额 | 沿用 p2p3 冻结值 | 任务化设定（继承冻结） |
| `155_009` | 期望参数量 | 台账 §五「按源码逐层计算」：嵌入 `40×128=5,120` ＋ `channel_adjust 128×128×1+128=16,512` ＋ 双 Conv1d `128×128×4+128=65,664`×2 ＋ `Linear(2048,1)=2,049` | 本文件实例化后**实测断言** |
| `200_000` | 参数量上限 | 用户简报冻结 | 门禁断言 |

判据与面板（**与 `official_p2p3.py` 完全一致，不改**）
--------------------------------------------------------------------------
- 主判据面板 `maskdga-half`；判据：**对抗面板 AP 提升 且 干净 FPR 不增**。
  `verdict` 沿 official 的字段结构（`panel`／`adv_AP`／`clean_FPR`／`adv_FNR`／`k2_reference_FNR`），
  臂对按 B-ResNet 链替换为 `D_vs_A`／`F_vs_D`／`G_vs_A`，判据本身**不新增、不放宽**。
  官方 `P2_pass`（B vs A）／`P3_pass`（C vs B）依赖 B／C 臂，本脚本不实现这两臂，故不出这两个键。
- 评价三面板：干净 `T18 val`、CharBot k=2 变体、MaskDGA 半替换近似变体，
  外加 official 既有的 `krand` 面板。**四面板的构造顺序、随机种子与算子逐行复用
  `official_p2p3.main`**（同一 `random.Random(42)`、同一调用次序）⇒ 两骨干的评价样本
  **逐字相同**，架构差异是唯一差量。
  > ⚠️ 如实登记（**不改**）：official 的 `krand` 面板与 `k2` 面板**用的是同一算子 `perturb2`**
  > （注释写作「k∈U{1..4}」，实现是固定 2 位替换），二者差异仅来自 rng 状态推进。
  > 本脚本按冻结口径**原样复现**，不修改；该差异归 `official_p2p3.py` 处置。
- 训练数据：`T17 train` 前 `30000`/类（与 screening 一致；`--dry-run N` 取前 `N`/类）。
- 断点：每臂完成后原子落盘（`*.tmp` 写完再 `replace`），`--dry-run` 走同一路径。

产出
--------------------------------------------------------------------------
`bresnet-p2p3-DRYRUN.json`（干跑）／`bresnet-p2p3-result.json`（全量），默认落本文件同目录，
`BRESNET_P2P3_OUT` 可覆盖。**不写入 `official_p2p3.py` 的 `P2P3_OUT` 文件**。

用法
--------------------------------------------------------------------------
    PYTORCH_ENABLE_MPS_FALLBACK=1 /opt/miniconda3/envs/rwkv/bin/python bresnet_p2p3.py \
        --dry-run 200 --arms A
    python bresnet_p2p3.py --arms A,D,F,G        # 全量（服务器 CUDA）
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# 臂框架复用：official_p2p3.py 为**本仓库自有代码**（非 AGPL 来源），
# 复用其 perturb2／perturb_half／load_split，保证对抗变体字符串与数据切分逐字一致。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import official_p2p3 as off

OUT = Path(os.environ.get("BRESNET_P2P3_OUT", Path(__file__).resolve().parent))
DATA = off.DATA
DEVICE = off.DEVICE
BATCH = off.BATCH                  # 128，论文 §3.2 p.3
EVAL_BATCH = off.EVAL_BATCH        # MPS 128／CUDA 1024，只影响吞吐不改指标
autocast_ctx = off.autocast_ctx    # 数值策略与 DRIFT 侧一致（CUDA bf16／MPS fp32）
SEED = off.SEED                    # 42
EPOCHS = off.EPOCHS                # 3
LR = 1e-3                          # 全参数单 lr：论文未明示，任务化设定（简报冻结，未验证）
SEQ_LEN = 63                       # 官方代码默认「Use 63 for e2LDs」
VOCAB_SIZE = 40                    # §7.2：nn.Embedding(40, 128)
EMBED_DIM = 128
N_BLOCKS = 1                       # 论文 §3.2「a single residual block」；图注「6 Residuals」不采用
KERNEL = 4
POOL_KERNEL = 4
POOL_PADDING = 2
N_CAND = 4                         # 组件 1：每恶意样本 K=4 变体一组
TOP_Q = 64                         # 组件 1：跨组 top-64 入批
W_BENIGN_FP = 3.0                  # 组件 2：被判恶意的真良性样本 CE 权重
BRESNET_N_PARAMS_EXPECTED = 155_009   # 台账 §五登记值
BRESNET_N_PARAMS_MAX = 200_000        # 简报冻结上限

# 字符表（40 项）：小写字母 26 ＋ 数字 10 ＋ `-` `_` `.` `~`。§7.2／台账 §五登记为 40 项。
# 索引顺序**未登记**（论文与台账只给字符集与「左零填充」，未给映射顺序）⇒ 任务化设定。
# 0 号槽给 `~`：2026-09-11 实测 T17/T18 本臂实际使用的 7.5 万条 eSLD 字符集为
# `-.0123456789a-z` 共 38 项，**`~` 与 `_` 零出现**，故 0 号槽（左零填充位）实际不与真实字符冲突。
CHARS = "~" + "abcdefghijklmnopqrstuvwxyz" + "0123456789" + "-_."
assert len(CHARS) == VOCAB_SIZE and len(set(CHARS)) == VOCAB_SIZE
char2ix = {c: i for i, c in enumerate(CHARS)}
PAD_IX = 0                         # 论文 §3.1「左零填充」；本表 0 号槽 = `~`（实测零出现）
assert CHARS[PAD_IX] == "~"


def encode(domains) -> np.ndarray:
    """B-ResNet 输入编码：40 项字符表 ＋ 长度 63 ＋ 左零填充（论文 §3.1 口径）。

    与 DRIFT 侧 `official.encode_char` 是**不同词表／不同长度／无 [CLS]/[SEP]**，
    见 §7.4 接口差异表。表外字符（实测零出现）映射到 0 号槽。
    """
    out = np.full((len(domains), SEQ_LEN), PAD_IX, dtype=np.int64)
    for row, d in enumerate(domains):
        # 论文 §3.1 明确输入先小写；本数据实测已全小写，`.lower()` 为幂等保险。
        ids = [char2ix.get(c, PAD_IX) for c in str(d).lower()[:SEQ_LEN]]
        out[row, SEQ_LEN - len(ids):] = ids      # 左填充（pad 在左，域名右对齐）
    return out


class ResidualITsec(nn.Module):
    """残差块：`conv1 → ReLU → conv2 → 与输入相加`（§7.2 块内结构）。

    `channel_adjust` 为 1×1 跳连通道对齐，**仅当 in≠out 时生效**（§7.2）；
    本配置 `128 == 128` ⇒ 前向不生效，但它作为模块常驻，其 16,512 参数计入
    台账 §五的 155,009 登记值。无 BN（§7.2 未列，登记参数量亦不含 BN 参数）。
    激活 = ReLU（§7.2 明确）；初始化 = PyTorch 默认（论文未明示，任务化设定）。
    """

    def __init__(self, in_channels: int = EMBED_DIM, out_channels: int = EMBED_DIM,
                 kernel_size: int = KERNEL) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size, stride=1, padding="same")
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, stride=1, padding="same")
        self.channel_adjust = nn.Conv1d(in_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x if self.in_channels == self.out_channels else self.channel_adjust(x)
        out = F.relu(self.conv1(x))
        out = self.conv2(out)
        return out + residual


class BResNet(nn.Module):
    """B-ResNet：单残差卷积块 ＋ max-pool ＋ `Linear(2048, 1)`，**输出 logits**（单分支）。"""

    def __init__(self, vocab_size: int = VOCAB_SIZE, embed_dim: int = EMBED_DIM,
                 seq_len: int = SEQ_LEN, n_blocks: int = N_BLOCKS,
                 pool_kernel: int = POOL_KERNEL, pool_padding: int = POOL_PADDING) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.blocks = nn.ModuleList(
            [ResidualITsec(embed_dim, embed_dim, KERNEL) for _ in range(n_blocks)])
        self.pool_kernel = pool_kernel
        self.pool_padding = pool_padding
        # ceil(seq_len / pool_kernel) = ceil(63/4) = 16 ⇒ 128 × 16 = 2048
        n_feat = embed_dim * (-(-seq_len // pool_kernel))
        self.classifier = nn.Linear(n_feat, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """`x`: [B, SEQ_LEN] int64 → logits [B, 1]。"""
        h = self.embedding(x).permute(0, 2, 1)               # [B, L, 128] → [B, 128, L]
        for blk in self.blocks:
            h = blk(h)
        h = F.relu(h)
        h = F.max_pool1d(h, kernel_size=self.pool_kernel, padding=self.pool_padding)
        return self.classifier(h.reshape(h.shape[0], -1))    # [B, 1]


def p_mal(logits: torch.Tensor) -> torch.Tensor:
    """单 logit → 恶意概率。`sigmoid(z)` 等价于 `[0, z]` 上 2 类 softmax 的第 1 维，
    与 DRIFT 侧 `p[:, 1]` 同口径；差异仅在 DRIFT 用中和均值走 `diag.probabilities`（本臂无该结构）。"""
    return torch.sigmoid(logits.float().reshape(-1))


def score(model: nn.Module, domains: list[str], batch: int = EVAL_BATCH) -> np.ndarray:
    """对任意域名列表打分（评价面板与组件 1 候选打分共用）。"""
    out = []
    with torch.inference_mode():
        for i in range(0, len(domains), batch):
            x = torch.from_numpy(encode(domains[i:i + batch])).to(DEVICE)
            with autocast_ctx():
                lg = model(x)
            out.append(p_mal(lg).cpu().numpy())
    return np.concatenate(out) if out else np.zeros(0, dtype=np.float64)


def metrics(model: nn.Module, domains: list[str], labels01: np.ndarray) -> dict:
    """评价面板指标：字段与 `official_p2p3.metrics` 对齐（AP/FPR/FNR/F1/FP/FN/n）。"""
    from sklearn.metrics import average_precision_score
    s = score(model, domains)
    pred = s >= 0.5
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum()); fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum()); tn = int((~pred & ben).sum())
    return {"AP": float(average_precision_score(labels01, s)),
            "FPR": fp / max(fp + tn, 1), "FNR": fn / max(fn + tp, 1),
            "F1": tp / max(tp + 0.5 * (fp + fn), 1), "FP": fp, "FN": fn, "n": len(s)}


def load_split(limit: int) -> tuple[list[str], np.ndarray]:
    """与 `official_p2p3.load_split` 同源（T17 train 前 `limit`/类）。"""
    return off.load_split(limit)


def train_arm(arm: str, train_d: list[str], train_y: np.ndarray,
              eval_clean: tuple[list[str], np.ndarray],
              eval_adv: tuple[list[str], np.ndarray],
              epochs: int) -> dict:
    """四臂训练（A／D／F／G），臂语义逐行对应 `official_p2p3.train_arm`：
      A = 干净训练；D = 组件 1（K=4 组内 fooled−组均值 → 跨组 top-64 入批）；
      F = D ＋ 组件 2（被判恶意的真良性样本 CE×3.0）；G = 只组件 2（无对抗增广）。
    """
    # 每臂重设 torch 全局种子 ⇒ 四臂共享**同一份初始权重**，臂间差量只剩机制本身。
    # （official_p2p3 的同一性质来自「四臂都从同一 checkpoint 加载」，B-ResNet 从头训练，
    #   故显式重设种子复现该性质；未重设则 A/D/F/G 会各自取到不同的随机初始化。）
    torch.manual_seed(SEED)
    model = BResNet().to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    assert n_params == BRESNET_N_PARAMS_EXPECTED, \
        f"参数量 {n_params} != 台账登记值 {BRESNET_N_PARAMS_EXPECTED}"
    assert n_params <= BRESNET_N_PARAMS_MAX, f"参数量 {n_params} 超上限 {BRESNET_N_PARAMS_MAX}"
    # 全参数单 lr：B-ResNet 为 155K 参数从头训练，无预训练分层需求（简报冻结，见模块 docstring 数值登记）
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    print(f"[{arm}] B-ResNet {n_params} 参数（断言 = 台账登记 {BRESNET_N_PARAMS_EXPECTED}），"
          f"单 lr {LR:g} 全参数训练，{len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    fpr_curve: list = []
    ec, ey = eval_clean
    ea, eay = eval_adv
    rng = random.Random(SEED)          # 与 official 同种子：变体字符串逐字一致
    adv_cache: dict[int, list[str]] = {}
    n = len(train_d)
    for ep in range(1, epochs + 1):
        model.train()
        order = list(range(n)); random.Random(SEED + ep).shuffle(order)
        t0 = time.time()
        nb = (n + BATCH - 1) // BATCH
        for bi in range(nb):
            idx = order[bi * BATCH:(bi + 1) * BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            if arm in ("D", "F"):
                # 组件 1（GFPO 2508.09726 §3 式(2) + Drichel 2024 §4.4.2 配比锚点）：
                # 每恶意样本 K=4 变体一组，组内 fooled（当前模型判良性）为优势，
                # 「fooled − 组均值」降序取跨组 top-64 入批，被拒变体零梯度。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache:
                        base = off.perturb2(train_d[i], rng)
                        adv_cache[i] = [off.perturb2(base, rng) for _ in range(N_CAND)]
                    for v in adv_cache[i]:
                        cands.append(v)
                        cand_owner.append(i)
                adv_batch: list[str] = []
                if cands:
                    model.eval()
                    p_cand = score(model, cands)
                    model.train()
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: -t[0])
                    adv_batch = [cands[j] for _, j in scored[:TOP_Q]]
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            # MPS 带梯度反向 batch 上限 128（与 official 同）：拼接变体后 192，
            # 用 128 子批梯度累积等效实现同一拼接大 batch 的（加权）平均损失，不改优化语义
            y_t = torch.from_numpy(batch_y).long().to(DEVICE)
            opt.zero_grad(set_to_none=True)
            loss_log = 0.0
            n_tot = len(batch_d)
            for s in range(0, n_tot, BATCH):
                sub_d = batch_d[s:s + BATCH]
                sub_y = y_t[s:s + BATCH]
                x = torch.from_numpy(encode(sub_d)).to(DEVICE)
                with autocast_ctx():
                    logits = model(x)
                p_ = p_mal(logits)
                # 与 DRIFT 侧 CE 同值：bce_with_logits(z, y) ≡ cross_entropy([0, z], y)
                ce = F.binary_cross_entropy_with_logits(
                    logits.float().reshape(-1), sub_y.float(), reduction="none")
                if arm in ("F", "G"):
                    # 组件 2：batch 内当前模型判恶意的真良性样本 CE ×3.0（权重为任务化设定，
                    # 无文献精确值；沿用 p2p3 冻结值，对冲 64 变体配额的恶意侧压力量级）
                    fooled_b = (p_ >= 0.5) & (sub_y == 0)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled_b] = W_BENIGN_FP
                    loss_s = (ce * w).sum() / n_tot
                else:
                    loss_s = ce.sum() / n_tot
                loss_s.backward()
                loss_log += loss_s.item()
            opt.step()
            if bi % 20 == 0:
                eta = (time.time() - t0) / (bi + 1) * (nb - bi - 1)
                print(f"[{arm} 心跳] epoch {ep} 批 {bi+1}/{nb} loss={loss_log:.4f} ETA {eta/60:.1f} min",
                      file=sys.stderr, flush=True)
        # 逐 epoch 干净 FPR 曲线（与 official 同：识别验证损失上升段，防瞬态误判）
        model.eval()
        fpr_now = metrics(model, ec, ey)["FPR"]
        fpr_curve.append({"epoch": ep, "clean_FPR": fpr_now})
        print(f"[{arm} 里程碑] epoch {ep}/{epochs} 完成，干净 FPR={fpr_now:.4f}（{time.time()-t0:.1f}s）",
              file=sys.stderr, flush=True)
    model.eval()
    clean = metrics(model, ec, ey)
    adv = metrics(model, ea, eay)
    return {"clean": clean, "adv": adv, "n_params": n_params, "fpr_curve": fpr_curve, "_model": model}


def main(dry: int = 0, arms_arg: str | None = None) -> None:
    torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
    tr_d, tr_y = load_split(dry if dry else 30000)
    import pyarrow.parquet as pq
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_benign_val.parquet").to_pylist()[:(dry or 7500)]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:(dry or 7500)]
    ec = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    ey = np.asarray([0] * len(tb) + [1] * len(td), dtype=bool)
    # 评价面板构造：与 official_p2p3.main 逐行同序（同 rng、同调用次序）⇒ 与 DRIFT 侧逐字相同的样本
    rng = random.Random(SEED)
    ea_k2 = [off.perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    ea_krand = [off.perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    ea_mask = [off.perturb_half(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    eval_clean = (ec, ey)
    adv_panels = {"k2": (ea_k2, np.ones(len(ea_k2), dtype=bool)),
                  "krand": (ea_krand, np.ones(len(ea_krand), dtype=bool)),
                  "maskdga": (ea_mask, np.ones(len(ea_mask), dtype=bool))}
    eval_adv_k2 = adv_panels["k2"]
    print(f"[B-ResNet P2/P3] 词表 {VOCAB_SIZE}、序列长 {SEQ_LEN}、字符表 {CHARS!r}；"
          f"训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}/maskdga {len(ea_mask)}",
          file=sys.stderr, flush=True)

    arms = tuple(arms_arg.split(",")) if arms_arg else (("A",) if dry else ("A", "D", "F", "G"))
    epochs = 1 if dry else EPOCHS
    results: dict = {}
    for arm in arms:
        t0 = time.time()
        r = train_arm(arm, tr_d, tr_y, eval_clean, eval_adv_k2, epochs)
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        results[arm] = r
        for pname, (pa, pay) in adv_panels.items():          # 逐臂四面板评价
            results[arm][f"adv_{pname}"] = metrics(arm_model, pa, pay)
        print(f"[里程碑] {arm}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} "
              f"adv={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv'].items()})}",
              file=sys.stderr, flush=True)

    verdict = _verdict(results)
    spec = {"backbone": "B-ResNet", "n_params": BRESNET_N_PARAMS_EXPECTED,
            "vocab_size": VOCAB_SIZE, "seq_len": SEQ_LEN, "chars": CHARS,
            "n_blocks": N_BLOCKS, "lr": LR, "batch": BATCH, "epochs": epochs, "seed": SEED,
            "loss": "binary_cross_entropy_with_logits", "optimizer": "Adam(weight_decay=0)",
            "prob_mapping": "sigmoid(single_logit)（无 classifier_head 融合，无中和均值）",
            "arms": list(arms)}
    out_name = "bresnet-p2p3-DRYRUN.json" if dry else "bresnet-p2p3-result.json"
    payload = {"spec": spec, "results": results, "verdict": verdict}
    tmp = OUT / (out_name + ".tmp")                          # 原子落盘（断点纪律）
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT / out_name)
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


def _cmp(base: dict, cand: dict, panel: str = "adv_maskdga") -> dict:
    """判据结构与 official P2/P3 同构：面板 AP 提升 且 干净 FPR 不增（判据不新增、不放宽）。"""
    return {"adv_AP_gain": round(cand[panel]["AP"] - base[panel]["AP"], 6),
            "clean_FPR_delta": round(cand["clean"]["FPR"] - base["clean"]["FPR"], 6),
            "pass": bool(cand[panel]["AP"] > base[panel]["AP"]
                         and cand["clean"]["FPR"] <= base["clean"]["FPR"])}


def _verdict(results: dict) -> dict:
    if len(results) < 2:
        return {"note": "dry-run 单臂"}
    panel = "adv_maskdga"
    v = {"panel": "maskdga-half",
         "criterion": "与 official_p2p3.py 同构：对抗面板 AP 提升 且 干净 FPR 不增（臂对按 B-ResNet 四臂链替换）",
         "adv_AP": {a: round(r[panel]["AP"], 4) for a, r in results.items()},
         "clean_FPR": {a: round(r["clean"]["FPR"], 4) for a, r in results.items()},
         "adv_FNR": {a: round(r[panel]["FNR"], 4) for a, r in results.items()},
         "k2_reference_FNR": {a: round(r["adv"]["FNR"], 4) for a, r in results.items()},
         "comparisons": {}}
    for tag, (base, cand) in (("D_vs_A", ("A", "D")), ("F_vs_D", ("D", "F")), ("G_vs_A", ("A", "G"))):
        if base in results and cand in results:
            v["comparisons"][tag] = _cmp(results[base], results[cand], panel)
    return v


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0, help="每类样本数（干跑 1 epoch）；0 = 全量")
    ap.add_argument("--arms", default=None, help="逗号分隔臂列表，如 A,D,F,G（默认全量 A,D,F,G／干跑 A）")
    a = ap.parse_args()
    main(dry=a.dry_run, arms_arg=a.arms)
