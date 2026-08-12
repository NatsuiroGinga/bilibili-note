---
title: "NetMamba+: A Framework of Pre-trained Models for Efficient and Accurate Network Traffic Classification"
authors:
  - Tongze Wang
  - Xiaohui Xie
  - Yong Cui
  - 等
year: 2026
date: 2026-08-08
journal: "arXiv:2601.21792v1（2026-01-29），IEEE 期刊投稿稿；ICNP 2024 版 NetMamba 的扩展"
source_pdf: "[[raw/papers/traffic-foundation-models/2601.21792_NetMamba+_改进版.pdf]]"
tags:
  - 流量基础模型
  - NetMamba
  - Mamba
  - 多模态
  - 长尾学习
  - 类型/论文
key_finding: "NetMamba+ 在原版之上加了三件事：包大小与到达间隔两路序列模态（早融合 + 正弦编码）、Flash Attention 版 NetTrans 块、长尾感知 LDA 损失；多模态是唯一带来大幅提升的部分（CipherSpectrum 0.8779→0.9652），而 Mamba 块本身相对 Flash-Attention Transformer 已无一致优势。"
---

# NetMamba+

> Wang 等, 2026, arXiv:2601.21792v1 · 15 页正文

## 一句话

同一课题组把 NetMamba 从"单模态字节 + Mamba"扩成"字节/包长/时间间隔三模态 + 可插拔骨干（Mamba 或 Flash-Attention Transformer）+ 长尾微调 + DPDK 在线系统"，其消融恰恰说明性能增益来自输入模态而非序列骨干。

## 论文证据

- 第 1—2 页摘要与引言：三项改进针对三个挑战——Transformer 效率、表示不充分、长尾分布；自述 F1 提升最高 6.44%，吞吐较最佳基线高 1.7 倍，在线系统平均吞吐 261.87 Mb/s。
- 第 4—5 页 §V：表示方案相对原版的**关键改动**——"所有包通过移除以太网头**以及掩码 IP 地址与端口**做匿名化"（原版只删以太网头）。其余保持 `Mb=5` 包、`Nh=80`、`Np=240`、`Lb=1600`、`Ls=4`、`L=401`（见第 10 页表 III）。
- 第 5 页 §V-5：新增"可插拔序列抽取"模态——取前 `Mseq=20` 个包的**包大小序列与到达间隔序列**（`Mseq > Mb`，即时序模态看得比字节模态更远）。包大小按 MTU 截断；间隔先取对数再过 sigmoid 归一到 [0,1]。
- 第 6 页 §VI-A-2：三模态早融合——包大小与间隔用**固定正弦编码**（而非线性投影，理由是线性投影抓不到相对变化与时间趋势），加模态段标识后与 stride 嵌入拼接，再加可学习位置嵌入。
- 第 6 页 §VI-B-1：Mamba 块相对原版"增加了一个外层残差连接"。
- 第 6—7 页 §VI-B-2：新增 NetTrans 块 = Flash Attention 2 + 前置归一化 + GeGLU FFN。
- 第 7 页 §VI-C-2：多模态预训练目标——stride 走 MAE 掩码重建（掩码率 0.9）；包大小与间隔 token 按 0.15 概率**置零而非移除**（对编码器全可见），包大小按离散值做交叉熵分类重建、间隔按连续值做 MSE 回归；总损失 `Lrec = Lstride-rec + Lsize-rec + Lint-rec`。
- 第 7—8 页 §VI-D-2 与式 (11)—(13)：LDA 损失 = Class-Balanced 重加权 `(1-β)/(1-β^{n_j})` × LDAM 边距 `Δ_j = C/n_j^{1/4}`。
- 第 8—9 页 §VIII-A-1 与表 II：**预训练语料换成 Browser（149,528 流，TLS1.3/GQUIC）与 Kitsune（167,831 流，攻击流量）两个数据集**，与微调集不再同源——这是相对原版最重要的方法论修正。微调集 11 个，含企业自有的 Huawei-VPN（38,704 流、12 类）与 CipherSpectrum、CSTNET-TLS1.3、CrossNet2021A、CP-Android、CP-iOS、CICIoT2022、USTC-TFC2016、ISCXVPN2016、DataCon2021-p1。表中还给出每集的加密流比例 EFR 与加密包比例 EPR（如 CICIoT2022 EFR 仅 0.0022）。
- 第 11 页表 IV：NetMamba+ 参数 PT 2.6M / FT 1.9M；CipherSpectrum AC 0.9652、CSTNET-TLS1.3 0.8498、CICIoT2022 0.9750、ISCXVPN2016 0.9460、USTC-TFC2016 0.9765。同表中 **TrafficFormer 表现很差**（CipherSpectrum 0.6071、ISCXVPN 0.6907），ET-BERT 也仅 0.7026/0.8900。作者明确指出：在全加密集上，仅用包长序列的 FS-Net（0.9000）就胜过多数深度与预训练模型。
- 第 11 页表 V（骨干消融）：NetMambaB（双向）0.9095 在 CipherSpectrum 上**高于** NetMamba 0.8779；NetMambaC（级联，32.7M）全面更差；NetTransV（vanilla）0.8504、NetTrans（Flash+GeGLU）0.8543、NetTransL（线性注意力）崩到 0.3754。即 Mamba 与优化版 Transformer 在五个集上互有胜负。
- 第 12 页表 VI（原版重做的字节消融）：去头部降 14.86%—47.50%；**去载荷 5 个数据集里 2 降 3 升**，作者明确写"payload 特征贡献不一致，若优先考虑效率，去掉载荷可能更好"；去 stride 切分（换二维 patch）最多降 2.27%；去预训练 4 个设定下降。
- 第 12—13 页图 6 与 §VIII-D：用 AMI 做模型无关的字段重要性分析，指出**总长度（第 2 个 stride）、协议（第 5 个）、TCP flags（第 17 个）、TCP 窗口大小（第 18 个）**重要性最高，头部 stride 显著高于载荷字节。
- 第 13 页表 VII（多模态消融，本文最强的正面证据）：CipherSpectrum 上 Byte Only 0.8779 / Size Only 0.8906 / Interval Only 0.7556 / All 0.9652；CSTNET-TLS1.3 上 0.7755 / 0.8112 / 0.5076 / 0.8498。但 CICIoT2022 上 All(0.9750) **低于** Byte Only(0.9769)，USTC-TFC 上 All(0.9765) 高于 Byte Only(0.9743) 但低于表 IV 中 NetTrans 的 0.9823。
- 第 13—14 页表 VIII（LDA 消融）：公开集最多提升 2.88%（CP-iOS NetTrans 0.6382→0.6670），Huawei-VPN 仅 0.79%；**CP-Android 上 NetTrans 加 LDA 反而从 0.7456 降到 0.7392**。
- 第 14 页表 IX（OOD）：以 CipherSpectrum 为 ID，用温度缩放熵做 OOD 检测，NetMamba+ AUROC 0.9455/0.9825/0.9720/0.9668；但 **Unknown Application 任务上 NetMamba+ 的 FPR95 = 0.3670，反而比 NetMamba 的 0.2744 更差**。
- 第 14 页 §VIII-I：在线系统 DPDK + 共享内存 + Redis，A30 GPU，`Wg=3s` 成批、`Wr=10s` 过期；批吞吐 29.85—335.21 Mb/s（均值 261.87），批延迟 0.02—5.68s（**均值 3.15s**）。
- 第 14 页 §VIII-J-1（分布漂移，本文最重要的负面数据）：按首包时间戳排序做时间切分后，CipherSpectrum 准确率仅降 0.42%，但 **CSTNET-TLS1.3 降 8.47%**；作者承认"NetMamba+ 在分布漂移下存在一定程度的性能退化，提升鲁棒性仍是未来工作"。

## 与本课题六个关注点的对照

- (a) 输入形态：三模态——字节（前 5 包 × 320B）、包大小序列、到达间隔序列（前 20 包）。**这是五篇里与"字段 + 时序统计"混合数据最接近的一个**，其"字节 stride + 正弦编码时序序列 + 段标识早融合"的拼装方式可直接迁移。
- (b) 有效历史：字节模态 5 包、时序模态 20 包；仍**无长度消融**，`Mseq=20` 的选择无依据说明。
- (c) 跨字段交互：AMI 分析（图 6）给出了字段级重要性的可复现测法，可直接用于本课题的字段交互诊断；但模型内部仍无显式跨字段机制。
- (d) 预训练目标与规模：三路重建（stride MSE + size CE + interval MSE），掩码率 0.9 / 0.15；语料 Browser + Kitsune 约 31.7 万流，150,000 步。
- (e) 评测缺陷：相对原版已修正预训练/微调同源问题；但时间切分下 CSTNET-TLS1.3 掉 8.47%，说明随机 8:1:1 划分的成绩含时间泄漏成分。
- (f) 可得性：代码仍指向 github.com/wangtz19/NetMamba；**NetMamba+ 权重是否发布、许可证均未在论文中说明**。

## 论文自陈局限与消融缺失

- 自陈：分布漂移下性能退化（§VIII-J-1）；只报告推理效率不报训练效率（§VIII-J-2）。
- 消融缺失：无 `Mseq` 长度扫描、无掩码率扫描、无模型规模缩放、无多种子/置信区间、无"多模态 + 骨干"的交叉消融（无法判断多模态收益是否依赖 Mamba）。
- 被回避的劣势：摘要"F1 提升最高 6.44%"未指明相对哪个基线与哪个数据集；三模态在 CICIoT2022 上劣于纯字节；LDA 在 CP-Android 上为负增益；OOD 的 FPR95 在一个任务上被更弱的 NetMamba 反超；在线系统平均延迟 3.15 秒，与"实时"叙事有距离。
- 数字口径：CipherSpectrum 0.8779→0.9652 按错误相对下降为 (0.1221-0.0348)/0.1221 = **+71.5%**，这是三模态输入而非骨干带来的。

## 允许主张

- 在同一表示与同一预训练目标下，**输入模态（包长、时间间隔）带来的收益远大于序列骨干的选择**；这是本课题"骨干替换"实验必须先控制的混淆因素。
- 单向 Mamba 相对 Flash-Attention + GeGLU 的优化版 Transformer 已无一致优势（表 V 五个集互有胜负）。
- 时序模态的具体工程做法（MTU 截断、log+sigmoid 归一、固定正弦编码、置零而非删除的重建目标）可直接复用。

## 禁止主张

- 不能把 NetMamba+ 的提升归因于 Mamba 或状态空间机制——消融指向多模态输入。
- 不能声称其在分布漂移下稳健——作者自己给出 8.47% 的跌幅。
- 不能把 261.87 Mb/s 说成低延迟在线检测能力，平均批延迟 3.15 秒。
- 不能假定 NetMamba+ 权重可得。

## 相关

- [[2024-Wang-NetMamba-高效流量分类状态空间]]（原版）
- [[2026-Beltiukov-netFound-协议感知流量基础模型]]
- [[2025-Zhou-TrafficFormer-流量预训练与数据增强]]（本文中表现最差的预训练基线之一）
