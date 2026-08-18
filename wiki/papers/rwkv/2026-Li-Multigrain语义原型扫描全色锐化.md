---
title: "Multigrain-aware Semantic Prototype Scanning and Tri-Token Prompt Learning Embraced High-Order RWKV for Pan-Sharpening"
authors:
  - Junfeng Li
  - Wenyang Zhou
  - Xueheng Li
  - Xuanhua He
  - Jianhou Gan
  - Wenqi Ren
year: 2026
date: 2026-08-13
journal: "arXiv 预印本（原件未标注会议或期刊）"
venue: "arXiv preprint"
arxiv: "2604.14622v1"
doi: "未在原件中定位"
source_pdf: "[[raw/papers/rwkv/2026_Multigrain_语义原型扫描重排序_全色锐化.pdf]]"
tags:
  - RWKV
  - 扫描顺序
  - 语义重排序
  - 全色锐化
  - 类型/论文
key_finding: "作者把 Vision RWKV 的固定双向光栅扫描判为「语义无关且带位置偏置」，改用 LSH 聚类得到的语义原型引导扫描顺序；但第 8 页表 2 显示全部四个组件累加只把 WV2 的 PSNR 从 42.0364 提到 42.3750（+0.34 dB），且第 7 页正文自称的增益（0.52/0.83/0.64 dB）与表 1 数字对不上。"
aliases:
  - Multigrain RWKV
  - Li2026-Pan-Sharpening-RWKV
related:
  - "[[2024-Duan-Vision-RWKV视觉双向扫描]]"
  - "[[2024-He-PointRWKV点云序列化]]"
  - "[[2025-Zhou-WKV共享随机打乱RWKV全色锐化]]"
---

# Multigrain 语义原型扫描：用聚类重排序替代 RWKV 的固定扫描顺序

> Li 等，arXiv:2604.14622v1（2026-04-16），原件 10 页

## 一句话

这篇论文的核心主张是：RWKV 在图像上的扫描顺序（固定双向光栅）本身是个设计缺陷，应该由内容语义决定处理顺序；实现方式是用局部敏感哈希（LSH）把语义相近的区域聚在一起再扫描，并配一套「三令牌」提示（全局令牌 + 原型令牌 + register 令牌）。

## 背景：问题的演进

- 第 1 页：Transformer 的 O(N²) 限制高分辨率遥感图像；Vision RWKV 提供线性替代，其空间混合为 `wkv = Bi-WKV(Ks, Vs)`，`Os = Mapping(σ(Rs) ⊙ wkv)`（式 1）。
- 第 1 页作者的问题陈述：`Bi-WKV(·)` 是「刚性规则的双向扫描策略」，存在位置偏置且缺乏语义引导。

## 方法核心

- **语义原型扫描**（第 1 页式 2、第 5 页式 12）：`Vs^index, index ← LSH(Vs)`，`Ks^index ← Cluster(Ks, index)`。第 5 页给出 LSH 形式 `h(⃗v) = (⃗a·⃗v + b)/r`，用一组平行超平面把欧氏近邻映到同一桶，从而让语义相关区域被连续处理。
- **三令牌提示**：全局令牌与聚类原型令牌提供语义先验，可学习的 register 令牌用于抑制噪声与伪影中间表示（第 1 页摘要）。
- **可逆 Q-Shift**（第 7 页）：把 Q-shift 放进可逆神经网络（INN）框架，`X1..X4 = Split(X)`，逐级 `Yi = Zi + Fi(Xi+1)`，最后 `Yo = Concate(Y1, Y2, Y3, Z4)`；论文称 Q-shift 在功能上等价于深度可分 3×3 卷积（`Q-shift ≡ DWC3×3`）但可无损变换。
- **中心差分卷积（CDC）**（第 7 页式 24—25）：`Oh = Os + CDC(Ks)`。作者的理由是 RWKV 的线性注意力在 token 级上等效于低通滤波，需要显式注入高频。
- 第 6 页式 18 给出对 `σ(Rs)` 的归一化约束 `0 < σ(Rs(i)) < 1`、`Σi σ(Rs(i)) = 1`。

## 实验结果

第 7 页表 1（WorldView-II / WorldView-III / GaoFen2，PSNR↑ SSIM↑ SAM↓ ERGAS↓）关键行：

| 方法 | WV2 PSNR | WV3 PSNR | GF2 PSNR |
|---|---|---|---|
| SFINet | 41.7244 | 30.5971 | 47.4712 |
| PanFlowNet | 41.8548 | 30.4873 | 47.2533 |
| Ours | 42.3751 | 31.3113 | 47.8941 |

第 8 页表 2 的组件消融（Momentum / Avg Token / Learn Token / Prototype）：

| 配置 | WV2 PSNR | WV2 SSIM | GF2 PSNR |
|---|---|---|---|
| 仅 Momentum | 42.0364 | 0.9716 | 47.5367 |
| + Avg Token | 42.1360 | 0.9723 | 47.6217 |
| + Learn Token | 42.2192 | 0.9730 | 47.6681 |
| Avg+Learn+Prototype（无 Momentum） | 42.2800 | 0.9733 | 47.7976 |
| 全部四项 | 42.3750 | 0.9737 | 47.8941 |

训练设置（第 7 页）：Adam，500 epoch，batch size 4，初始学习率 5×10⁻⁴，每 100 epoch 减半。

## 与本课题的关系

- **对应证据类 (a) 的反面参照：简单平均令牌的边际收益很小。** 表 2 中「Avg Token」（全局平均池化得到的令牌）单独叠加只带来 42.0364→42.1360（+0.0996 dB）。在这个任务上，简单池化不是主要收益来源；这与本课题「实体级简单聚合大幅优于逐流」的现象方向相反，**说明「池化优于复杂序列建模」不是普适规律，取决于任务的聚合粒度是否与标签粒度对齐**。全色锐化是逐像素回归任务，标签粒度即像素，聚合无处可省；本课题标签在实体级，聚合能直接消除逐流标签噪声。这是本课题推论，论文未讨论。
- **扫描顺序 = 排序先验，是可迁移机制。** 论文用 LSH 聚类决定「谁和谁相邻」再送进 RWKV，本质是在递归之前重排输入以让相关元素靠近。对本课题的对应假设（**待验证**）：实体内多条流按某种相似度而非时间戳排序后再做递归，是否能改善状态利用？论文未做任何序列/流量实验，不能引用其数字。
- 论文对 RWKV 线性注意力「等效低通滤波」的判断（第 7 页）提示：状态递归天然平滑高频，若本课题的攻击信号是短促突发，纯递归表示可能被平滑掉。这是论文的动机陈述，**不是实证结论**。

## 不可直接声称的内容与原件内部不一致

- 第 7 页正文写「our methods achieve PSNR improvements of 0.52 dB, 0.83 dB, and 0.64 dB relative to the highest-performing algorithm for the WorldView-II, GaoFen2, and WorldView-III datasets」。按第 7 页表 1 复算：WV2 为 42.3751 − 41.8548（PanFlowNet）= **0.5203 dB**（与 0.52 相符）；GF2 为 47.8941 − 47.4712（SFINet）= **0.4229 dB**（与 0.83 不符）；WV3 为 31.3113 − 30.5971（SFINet）= **0.7142 dB**（与 0.64 不符）。**引用时只能用表 1 复算值，不得引用正文的 0.83/0.64。**
- 第 7 页表 1 的 Ours PSNR 为 42.3751，第 8 页正文与表 2 为 42.3750，末位不一致。
- 论文未报告多次运行、种子或置信区间；未做参数量/FLOPs 对照，因此无法判断增益是否来自更大预算。
- 表 2 缺少「无 Momentum 且无 Prototype」等组合，四组件并非完整析因设计。

## 可引用的逐字原文

> "its conventional bidirectional raster scanning is still semantic-agnostic and prone to positional bias"（第 1 页摘要）

## 局限

- 只在三个全色锐化数据集上验证，没有跨传感器或跨年度的域偏移实验。
- LSH 聚类引入的额外开销与推断时的确定性（哈希随机性是否固定种子）原件未说明。
- 增益幅度（0.3—0.7 dB）与自报数字存在不一致，削弱了结论强度。

## 疑问 / 待验证

- 语义扫描相对随机重排、相对原始光栅扫描的单独消融未给出（表 2 的四项都不是「扫描顺序」本身）——即论文的第一大卖点没有独立消融。
- register 令牌抑制伪影的说法只有第 8 页图 7 的定性特征分析支持，无定量证据。

## 文献信息

- arXiv:2604.14622v1 [cs.CV]，2026-04-16。原件未标注会议或期刊。
- 原件：`raw/papers/rwkv/2026_Multigrain_语义原型扫描重排序_全色锐化.pdf`，10 页，SHA-256 `f318eb5c4cb9461d0d5953451be399b0558510dc084b493739855310d93e2aaf`。
- DOI：未在原件中定位。
