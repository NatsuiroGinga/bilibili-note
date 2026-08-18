---
title: "Vision-RWKV: Efficient and Scalable Visual Perception with RWKV-Like Architectures"
authors:
  - Yuchen Duan
  - Weiyun Wang
  - Zhe Chen
  - Xizhou Zhu
  - Lewei Lu
  - Tong Lu
  - Yu Qiao
  - Hongsheng Li
  - Jifeng Dai
  - Wenhai Wang
year: 2024
date: 2026-08-13
journal: "ICLR 2025（原件页眉 Published as a conference paper at ICLR 2025；arXiv 版 2024 年首发）"
venue: "ICLR 2025"
arxiv: "2403.02308v3"
doi: "未在原件中定位"
source_pdf: "[[raw/papers/rwkv/2024_Duan_Vision-RWKV_视觉双向扫描.pdf]]"
tags:
  - RWKV
  - 视觉骨干
  - 双向扫描
  - 因果性假设
  - 类型/论文
key_finding: "在非因果的图像数据上，原版单向因果 RWKV 注意力的 ImageNet Top-1 比作者的双向改造低 4.0 点（第 9 页表 5：RWKV 71.1 vs VRWKV-T 75.1）；把 RWKV 的因果状态递归直接搬到与因果顺序不匹配的数据上会显著掉点，必须改造输入的扫描/移位结构。"
aliases:
  - VRWKV
  - Duan2024-Vision-RWKV
related:
  - "[[RWKV-面向Transformer时代的循环语言模型]]"
  - "[[2025-Peng-RWKV7-Goose]]"
---

# Vision-RWKV：视觉领域的双向 RWKV 骨干

> Duan 等，ICLR 2025（arXiv:2403.02308v3，2025-03-31 版），原件 17 页

## 一句话

把 RWKV 用到图像上时，作者必须同时替换两处结构才能超过 ViT：一是把单向因果的 WKV 换成双向的 `Bi-WKV`，二是把单向 token shift 换成四方向 `Q-Shift`；消融显示原版因果 RWKV 注意力比完整模型低 4.0 点（第 9 页表 5）。

## 背景：问题的演进

- 第 1—2 页：ViT 的 O(N²) 复杂度限制高分辨率与长序列；NLP 侧的 RWKV 与 Mamba 提供线性替代，作者要把这套线性聚合搬到视觉。
- 第 2 页明确列出两处必须重新考虑的问题：空间聚合算子要按图像与文本的模态差异重新设计；以及 CUDA 级核需要重写。

## 方法核心

- 第 5 页式 (1)—(5)：空间混合用 `Rs = Q-ShiftR(X)WR` 等生成 R/K/V，注意力结果 `wkv = Bi-WKV(Ks, Vs)`；`Bi-WKV` 是双向求和形式，把 RWKV 原有的因果掩码去掉。
- 第 5 页两处细节：衰减项对时间差取绝对值（相对偏置），并强制衰减参数 `w` 为正，使指数项只衰减不增长。
- 第 6 页式 (8)：`FLOPs(Bi-WKV(K,V)) = 13 × T × C`，对 token 数线性。
- 第 6 页式：`Q-Shift(∗)(X) = X + (1 − µ(∗))X†`，用上下左右四个方向的邻域替代 RWKV 的单向前一 token 移位。
- 第 7 页 §3.4「Scale Up Stability」：为避免指数项溢出，把指数项除以 token 数，写成 `exp(−(|t − i| − 1)/T · w)`，并在注意力与 Squared ReLU 之后加额外 LayerNorm。这是一个明确的**长序列数值稳定性补丁**。

## 实验结果

分类（第 7 页表 2，ImageNet-1K）：

| 模型 | 分辨率 | 参数 | FLOPs | Top-1 |
|---|---|---|---|---|
| DeiT-T | 224² | 5.7M | 1.3G | 72.2 |
| VRWKV-T | 224² | 6.2M | 1.2G | 75.1 |
| ViT-L | 384² | 309.5M | 191.1G | 85.2 |
| VRWKV-L | 384² | 334.9M | 189.5G | 86.0 |
| VRWKV-L⋆（Bamboo-47K 预训练） | 384² | 334.9M | 189.5G | 86.5 |

检测/分割（第 8 页表 3，COCO val2017）：VRWKV-T 41.7 APb / 38.0 APm，ViT-T 加窗注意力 41.1 / 37.5；第 8 页正文称 VRWKV-T 骨干 FLOPs 比加窗 ViT-T 低约 30%，APb 高 0.6 点。语义分割（第 9 页表 4，ADE20K）：VRWKV-S 47.2 mIoU vs ViT-S 46.2 mIoU，FLOPs 降 14%；VRWKV-L 53.5 vs ViT-L 53.4。

**本课题最关心的消融（第 9 页表 5，ImageNet-1K 从零训练，Tiny 规模）**：

| 变体 | Token Shift | 双向注意力 | Top-1 |
|---|---|---|---|
| RWKV（原版） | original | ✕ | 71.1（−4.0） |
| Variant 1 | none | ✓ | 71.5（−3.6） |
| Variant 2 | original | ✓ | 74.4（−0.7） |
| Variant 3 | Q-Shift | ✕ | 72.8（−2.3） |
| VRWKV-T | Q-Shift | ✓ | 75.1 |

第 9 页正文：去掉双向（Variant 3 → VRWKV-T）带来 2.3 点差距；第 9 页 ERF 分析称「RWKV Attn」在 1024×1024 输入下中心像素无法关注到图像底部。

## 与本课题的关系

- **对应证据类 (b)：因果/顺序假设不匹配时的受控退化测量。** 表 5 是一次严格控制参数量与训练配置的消融：只把双向换回 RWKV 原版因果注意力，Top-1 从 75.1 掉到 72.8（−2.3）；再把 Q-Shift 换回原版单向 shift，掉到 71.1（−4.0）。这与本课题「完整 RWKV-7 状态递归反而更差」的实测现象是同一类：**RWKV 的状态递归带有强因果顺序先验，当数据的真实结构不是该顺序时，递归不是增益而是负担。**
- 可迁移机制（**待验证假设，非论文结论**）：LSPR23→24 的流内包序列是真因果的，但一个实体（2-IP 对）内部的多条流之间不必然有强顺序语义。若把实体级序列当成「无序集合」，则本文的结论支持用对称/双向或池化聚合替代单向递归。本文没有做任何网络流量实验，不能据此声称对 LSPR 有效。
- 第 7 页的有界指数（除以 T）与额外 LayerNorm 是可直接借用的**数值稳定性工程手段**，本课题若继续用长前缀状态递归可以对照；但论文只在图像分辨率放大场景验证，未验证跨年度分布漂移。

## 不可直接声称的内容

- 不能说「双向优于因果」是普适结论：本文只在图像（本身无因果顺序）上验证。
- 不能把 ImageNet/COCO/ADE20K 的增益迁移为任何检测指标（AP、DR@FPR）的预期。
- 论文未做任何分布漂移或跨年度实验，与本课题证据类 (b) 只是**机制类比**，不是同任务证据。

## 可引用的逐字原文

> "VRWKV-T has approximately 30% lower backbone FLOPs compared to ViT-T using window attention"（第 8 页 §4.2 Results）

## 局限

- 第 10 页承认 Q-Shift 的 PyTorch 实现效率很低；`Bi-WKV` 缺乏 Nvidia 张量核级优化，只在高分辨率场景相对 flash attention 有速度优势。
- 全部实验限于视觉三任务，没有语言、时序或网络数据的对照。
- 表 5 只在 Tiny 规模做，未验证消融结论在 -L 规模是否保持。

## 疑问 / 待验证

- 双向带来的 2.3 点里，多少来自「非因果」本身，多少来自感受野翻倍？论文未做等感受野对照。
- 有界指数 `exp(−(|t−i|−1)/T·w)` 把衰减与序列长度耦合，这在变长流序列上会不会引入长度偏置？原件未讨论。

## 文献信息

- arXiv:2403.02308v3 [cs.CV]，2025-03-31。
- 原件：`raw/papers/rwkv/2024_Duan_Vision-RWKV_视觉双向扫描.pdf`，17 页，SHA-256 `97b67f08fa033269d4b5128e754fba3438f6a59a96b1199e602cb56498246789`。
- 代码地址（原件第 1 页给出）：https://github.com/OpenGVLab/Vision-RWKV 。
- DOI：未在原件中定位。
