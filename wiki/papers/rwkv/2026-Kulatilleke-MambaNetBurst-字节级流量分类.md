---
title: "MambaNetBurst: Direct Byte-level Network Traffic Classification without Tokenization or Pretraining"
authors:
  - Gayan K. Kulatilleke
  - Siamak Layeghy
  - Mahsa Baktashmotlagh
  - Marius Portmann
year: 2026
date: 2026-08-07
journal: "arXiv:2605.11034v1 [cs.CR]，2026-05-11 提交（预印本，未见正式发表信息）"
source_pdf: "[[raw/papers/rwkv/2026_Kulatilleke_MambaNetBurst_字节级流量分类.pdf]]"
zotero_key: "LHMCT94Z"
tags:
  - Mamba
  - Mamba2
  - 线性循环模型
  - 网络流量
  - 加密流量
  - 状态容量
  - 类型/论文
key_finding: "在 1600 字节的 burst 级流量分类上，早期下采样（stride）造成的损失远大于状态转移矩阵的表达力差异；dstate 16—64 已足够，增到 128 反而变差；Mamba-2 的 scalar×I 转移在该模态上不劣于 Mamba-1 的对角转移，且更稳定更快。"
---

# MambaNetBurst 字节级流量分类

> Kulatilleke 等（University of Queensland），2026，arXiv:2605.11034 · 预印本

## 一句话

MambaNetBurst 用 4 层 Mamba-2 直接吃原始报文字节，不做分词、不做 patch、不做自监督预训练，在六个公开基准上打平或超过更重的预训练基线；其消融把"表达力瓶颈在哪"这一问题给出了明确答案：不在状态转移结构，而在输入端的早期信息损失。

## 论文原结论（含页内位置）

### 方法（第 III 节，PDF 正文"Architecture"）

- 输入构造（III-A）：按五元组切流，取前 `n = 5` 个包，每包取前 `m = 320` 字节，拼成 1600 字节固定序列；保留包边界，聚焦每包最前部的头部与初始载荷。
- 偏差控制（III-A"Bias control and masking"）：IP 地址置为 `0.0.0.0`，删除以太网头，排除 ARP/DHCP 等非 IP 协议，train/val/test 按流级切分防重叠。
- 嵌入（III-B、III-C）：256 符号词表的可学习字节嵌入，`d_model = 256`；再接两层 GELU 投影 MLP `ẽ_i = W₂ ϕ(W₁ e_i)`（式 3），动机取自 MambaByte。
- 分类头（III-D、III-E）：序列尾部追加可学习 CLS token 并加可学习位置嵌入（式 4）；堆 `N = 4` 个 Mamba-2 块，取 CLS 位置的最终状态过 softmax（式 5、6），交叉熵训练（式 7）。
- Mamba-2 块前向见 Algorithm 1：`z, x, B, C, Δ` 并行投影 → Conv1d+SiLU 局部混合 → `Discretize(Δ, A, B)` → SSD（`Q=C, K=B̄, V=x_conv`）→ `y ⊙ SiLU(z)` 门控 → 输出投影加残差。

### 实验设置（第 IV 节）

六个公开基准：CrossPlatform(Android/iOS)、ISCXVPN2016、ISCXTor2016、USTC-TFC2016、CICIoT2022。基线数值直接引自 NetMamba 论文。硬件为单张 RTX 3090（23.54 GiB），Mamba 系 batch 128，Transformer 系因显存只能 batch 32；120 epoch，AdamW，lr 1e-3，10 epoch 线性 warm-up + 余弦退火。

### 主结果（Table II、Table III）

MambaNetBurst（2.5—2.7M 微调参数、无预训练）在 CrossPlatform(Android) F1 0.9824、iOS 0.9851、CICIoT2022 0.9966、ISCXTor2016 0.9990、ISCXVPN2016 0.9871、USTC-TFC2016 0.9954；对照 NetMamba（2.2M 预训练 + 1.9M 微调）分别为 0.9096 / 0.9305 / 0.9929 / 0.9986 / 0.9806 / 0.9957。差距主要出现在 CrossPlatform 两个多类别（253/254 类）数据集上。

### 消融（Table IV，六数据集 macro-F1 的 AVG/MIN/MAX/VAR）

| 变体 | AVG | MIN | VAR |
| --- | --- | --- | --- |
| Std pos（默认） | 0.9909 | 0.9824 | 4.77e-5 |
| Without pos enc | 0.9904 | 0.9810 | 5.53e-5 |
| Std pos (Mamba-1) | 0.9874 | 0.9769 | 9.21e-5 |
| Stride(4) | 0.9772 | 0.9524 | 4.51e-4 |
| Stride(2) | 0.9823 | 0.9709 | 1.27e-4 |
| No emb proj | 0.9894 | 0.9799 | 5.79e-5 |
| 2 layers | 0.9878 | 0.9782 | 7.97e-5 |
| 1 layer | 0.9870 | 0.9722 | 9.82e-5 |
| d_state 32 | 0.9879 | 0.9791 | 4.55e-5 |
| d_state 64 | 0.9883 | 0.9769 | 6.52e-5 |
| d_state 128 | 0.9849 | 0.9612 | 2.18e-4 |
| Compact(64/64/2) | 0.9821 | 0.9618 | 2.12e-4 |
| Compact(32/32/2) | 0.9615 | 0.9060 | 1.48e-3 |
| Transformer | 0.9788 | 0.9289 | 6.69e-4 |
| Linear Tr (FlashAttn-2) | 0.9925 | 0.9868 | 2.19e-5 |

论文据此给出三条结论（第 IV-B 节小标题与第 VII 节 Conclusion）：保留字节级时间分辨率是关键；非 stride 设置下 Mamba-2 比 Mamba-1 更稳；`d_state` 16—64 与足够的 `d_model` 比一味加大状态更重要。作者同时声明 `d_conv` 与 expand 在 Table IV 中固定，相关结论只能是间接的。

### 效率（第 V-C、V-D 节与 Table V）

RTX 3090、2.5—2.7M 参数、序列长 1600：Mamba-2 反向平均快约 50%（论文另处表述为对 Mamba-1 快 30—60%），前向与推理快 8—20%；Mamba-2 在 batch 256 出现 OOM（存 chunk 中间量换速度），Mamba-1 用重计算省显存但更慢。Figure 2 称 Mamba-2 在 F1—推理时延上是 Pareto 最优；Linear Transformer + FlashAttention-2 的 F1 最高（0.9925）但推理明显更慢。

## 与本课题的关系（直接相关的四条证据）

1. **状态容量存在上界，不是越大越好。** `d_state` 从 16 → 32 → 64 变化很小，到 128 时 AVG 降到 0.9849、MIN 掉到 0.9612、方差涨到 2.18e-4。论文的解释（第 VI-D 节）是过大的状态容量在固定训练与正则预算下会过拟合数据集特有的长程伪特征，并把容量从主导判别的短中程结构上挪走。这与本课题"长时历史仅贡献 +6.0%"的先导结论方向一致。
2. **字段/局部结构的贡献远大于长程记忆。** stride(4) 是所有单因素消融中最坏的一个（AVG 0.9909 → 0.9772，MIN 0.9524，方差涨一个数量级）；论文第 VI-C 节明确写道主要经验瓶颈不是转移矩阵的灵活性，而是早期信息损失。这与本课题"窗口级字段交互 +30.1%"互为旁证。
3. **线性注意力/线性循环的表达力边界在该任务上不构成瓶颈。** Mamba-2 的 `A = αI`（所有状态维共享同一基础衰减率）理论上比 Mamba-1 的对角 `A`（每通道独立时间常数）弱，但第 VI-B 节的实验显示前者反而更稳；作者归因为多头结构、学习投影、输入相关参数、局部卷积与门控补偿了基础 A 的简化。也就是说，**通道混合与门控可以替代转移矩阵层面的多时间尺度**。
4. **位置编码近乎可有可无。** 去掉位置编码后 AVG 仅从 0.9909 降到 0.9904；论文认为因果卷积与递归状态动力学本身已提供顺序结构，位置编码的价值主要体现在降低跨数据集方差。

## 可迁移机制

- **状态容量扫描应作为消融必选项**：本课题若要论证 RWKV-7 的状态容量，应像本文一样报告 AVG/MIN/VAR 三个量而非只报均值——`d_state 128` 的退化只有在 MIN 和 VAR 上才明显。
- **"早期聚合 vs 原始分辨率"是可直接复用的对照轴**：把 stride/patch/分词作为受控变量，可以把"字段交互贡献"这一说法转成可证伪的实验设计。
- **无预训练的强监督基线**：本文说明在 burst 级流量任务上，端到端监督足以打平重预训练管线，可作为本课题设置基线预算时的参照。

## 不可直接声称

- 不得把本文的 macro-F1 数字迁移为本课题结果。本文任务是应用/类别识别与攻击流量分类，不是本课题的攻击状态检测。
- 不得把"Mamba-2 转移结构足够"外推为"RWKV-7 的 Delta 规则状态更新在本课题上足够"。两者架构与任务均不同，本文未评估任何 RWKV 模型。
- 不得把 RTX 3090、序列长 1600、2.5M 参数下的时延与显存数字迁移到 RTX 5090 或其他配置。
- 本文基线数值转引自 NetMamba 论文，未在同一环境复跑；跨方法比较的严格性受此限制。

## 仍需实验验证的假设

- **待验证**：在本课题的 RWKV-7 设置下，状态维度是否同样存在"中等最优、过大退化"的形态。本文只在 Mamba-2 的 `d_state` 上观察到，属于推论。
- **待验证**：本课题窗口级字段交互的 +30.1% 增益，是否与本文 stride 消融揭示的同一类"细粒度局部结构"机制同源。目前只是方向一致，无共同实验支撑。
- **待验证**：论文第 VI-F 节关于"去掉预训练可省 3—15 倍墙钟时间、显存降 2—4 倍"的说法为估算性表述，未给出独立计时表支撑（Table V 只对比 Mamba-1/2）。

## 局限与阅读风险

- 预印本，未见同行评审记录。
- Table IV 中 `F1:Std pos` 的 ISCXTor2016 单元带星号（0.9990*），原文未在表注中解释该星号含义。
- 正文有若干笔误（如 "torkenization"、VI-B 节两处并列项都标为 "(d)"），不影响主结论但说明稿件未经完整校对。

## 文献信息

- arXiv: https://arxiv.org/abs/2605.11034
- 官方 Mamba 实现引用：https://github.com/state-spaces/mamba
- 相关笔记：[[NetMamba-高效流量序列表征]]、[[ET-BERT-加密流量报文与突发表征]]、[[YaTC-多层流量表征]]
