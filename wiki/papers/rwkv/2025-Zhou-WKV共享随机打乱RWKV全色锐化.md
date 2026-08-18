---
title: "WKV-sharing embraced random shuffle RWKV high-order modeling for pan-sharpening"
authors: [Man Zhou, Xuanhua He, Danfeng Hong, Bo Huang]
year: 2025
date: 2026-08-13
journal: "NeurIPS 2025"
source_pdf: "[[raw/papers/rwkv/2025-Zhou-WKV-Sharing-Random-Shuffle-RWKV-Pansharpening-NeurIPS.pdf]]"
sha256: "4453011dc20f372c5d6122da38e31ef12264b76f6acaa2379fad96c8f32fbe01"
tags:
  - RWKV
  - 图像融合
  - 扫描顺序
  - 类型/论文
key_finding: "RS-RWKV 在 Vision RWKV 的空间混合器里，对每个 RWKV 层输入 WKV 注意力核的 Key/Value 序列做随机打乱（打乱后再逆打乱恢复位置），以蒙特卡洛期望近似消除固定扫描顺序带来的建模偏差；消融显示去掉随机打乱后 PSNR 下降约 0.18dB（Table 3，第 9 页），但该机制作用于完全可见的 2D 图像 token 序列，不涉及在线因果约束。"
method: "在 RWKV 空间混合器的 WKV 注意力计算前对 Key/Value 序列做随机 shuffle，计算后做逆 shuffle 恢复空间位置；配合蒙特卡洛平均近似对随机顺序的期望；并把 WKV 激活跨层共享（WKV-sharing）、把 channel-mixer 的一阶门控机制跨层共享以获得高阶建模能力。"
baseline: "SFIM/GS/Brovey/IHS/GFPCA 等传统全色锐化方法，PNN/PANNet/MSDCNN/SRPPNN/GPPNN/MutNet/INNformer/SFINet/PanFlowNet 等深度学习基线"
aliases:
  - RS-RWKV
  - Zhou2025-WKVsharing
---

# WKV-sharing embraced random shuffle RWKV high-order modeling for pan-sharpening

> Zhou, He, Hong, Huang, NeurIPS 2025，共 9 页正文（不含附录）。

## 一句话

RS-RWKV 针对 Vision RWKV 固定双向扫描顺序带来的建模偏差，提出对空间混合器的 Key/Value 序列做随机打乱（随机 shuffle）+ 逆打乱（inverse shuffle）+ 蒙特卡洛期望近似（M=1 已足够稳定），并把 WKV 激活与 channel-mixer 门控跨层共享以获得"高阶”建模能力；消融证明去掉随机打乱会损失约 0.18dB PSNR（Table 3，第 9 页）。

## 方法核心

- **背景问题**（第 1–2 页）：Vision RWKV 的空间混合器用递归双向扫描 `Re-WKV(.)`（Eq. 32–33）计算注意力，但递归扫描依赖固定的 token 排列顺序（图像被展平成 $T=H\times W$ 的一维序列），"suffers from biased effects and requires substantial processing time”。
- **随机打乱机制**（Eq. 6–9、39–42，第 3、6 页；Fig. 4，第 5 页）：
  - $(K_s, V_s) = \mathrm{RS}(K_s, V_s)$：对空间混合器输入的 Key/Value token 序列做随机重排（随机置换 $T$ 个 token 的顺序）；
  - $wkv = \mathrm{WKV}(K_s, V_s)$：在打乱后的顺序上做 WKV 递归计算；
  - $O_s = \mathrm{Mapping}(\sigma(R_s)\odot wkv)$，再 $O_s = \mathrm{IS}(O_s)$：用逆打乱把输出恢复回原始空间位置（IS 是 RS 的逆置换，用缓存的位置信息实现，第 6 页 Fig. 6 说明）。
  - 打乱作用于**每一个** RSRWKV 块的空间混合器（默认堆叠 $L=9$ 层，见 Table 2，第 9 页 "regular (L=9)"），不是只在网络某个固定位置打乱一次。
  - 蒙特卡洛期望估计（Eq. 10–11、43–44）：$O_s \approx \frac1M\sum_{i=1}^M[\mathrm{RS},\mathrm{WKV}]$，类比 Dropout 的测试期望思想，用多次随机打乱—计算—逆打乱的平均去逼近对所有排列的期望。
- **WKV-sharing 与高阶 channel-mixer**（Eq. 12–20、45–59，第 2、6–7 页）：作者论证 attention 本质上是一阶线性加权函数（$O_j=\mathrm{sigmoid}(R_c)\cdot V_c$，满足概率测度约束，Eq. 47–48），据此把 WKV 激活和门控机制跨 RWKV 层共享（Eq. 19–20、57–58），以更低延迟实现更高阶的跨层交互。

## 关键数字（附页码/表号）

- Table 1（第 8 页）：WordView-II/III、GaoFen2 三个全色锐化基准上，RS-RWKV 相比 PanFlowNet（此前最强基线）PSNR 分别提升 0.2397dB（42.0945 vs. 41.8548）、0.4792dB（30.9665 vs. 30.4873）、0.4611dB（47.7144 vs. 47.2533）。
- **Table 3（第 9 页，"Ablation studies on the proposed core designs”）——随机打乱的消融**：完整模型（Config V，含 KV-cache/Channel-mixer cache/Random shuffle/Random manifold loss）PSNR=42.0945、SSIM=0.9721、SAM=0.0214、ERGAS=0.9081；去掉 Random shuffle（Config III）PSNR=41.9172、SSIM=0.9713、SAM=0.0224、ERGAS=0.9274。即去掉随机打乱使 PSNR 下降 0.1773dB、SAM 变差 0.001、ERGAS 变差 0.0193——四个指标全部一致变差。
- 正文对该消融的定性解释（第 8–9 页）："Removing Random Shuffle introduced fixed-sequence biases, reducing feature diversity."
- **蒙特卡洛采样数消融**（Fig. 9，第 9 页附近段落）：把采样数 $M$ 从 1 扫到 32，性能"remained remarkably stable across this range”，作者最终选 $M=1$（单次随机打乱、不做多次平均）作为默认配置，兼顾效率与效果。

## 我的理解 / 与本课题的关系

这篇论文的证据结构是"去掉随机打乱 → 四个图像质量指标全部变差”，说明**任何单一固定扫描顺序对这个递归 WKV 核都会引入建模偏差**，而随机打乱（配合逆打乱恢复位置）能缓解这种偏差；这不等于"顺序对该任务完全不重要”，而是"没有哪个固定顺序是天然正确的，随机化能去掉对某个特定顺序的过拟合”。这个机制建立在**完全可见的 2D 空间输入**上（整张图像一次性可得，打乱与逆打乱在同一次前向传播内完成），与本课题"同一 2-IP 对内按时间排序"的**在线、因果**流序列有本质结构差异：图像的 token 排列只是把 2D 网格展平成 1D 的人为选择，$T!$ 种排列在语义上等价（都描述同一个 2D 空间关系）；而流量的时间顺序是真实的因果语义（握手先后、突发节奏），打乱后无法用"逆打乱”完整恢复，而且现实中的在线检测无法在打乱—计算—逆打乱这个闭环完成前就拿到全部未来数据。

## 局限

- 全部实验是全色锐化（图像融合）任务，指标为 PSNR/SSIM/SAM/ERGAS，没有涉及任何序列检测/分类任务。
- "顺序不重要”的证据只体现在"去掉随机打乱会变差”这一个方向，论文没有做"完全固定顺序 vs. 完全随机打乱 vs. 真实空间顺序”的三方对比，无法判断打乱后的性能是否仍然依赖某种残余的空间结构信息。
- 蒙特卡洛采样数消融（Fig. 9）说明 $M=1$ 已经足够稳定，但这是在同一次前向传播内、输入完全可见的前提下得出的结论，不能直接推广到需要多次独立观测的在线场景。

## 逐字引文

> "Removing Random Shuffle introduced fixed-sequence biases, reducing feature diversity." —— 第 8–9 页（Table 3 消融结果的定性解释）。

## 必答问题：能否搬到"同一 2-IP 对内按时间排序的流序列”上做顺序随机化消融？

**shuffle 具体打乱什么、在哪一层**：打乱空间混合器输入到 WKV 注意力核的 Key/Value token 序列（图像展平后的 $T=H\times W$ 个空间位置），逆打乱在同一空间混合器输出处恢复原始空间顺序（Eq. 6–9、39–42）。这一操作嵌入在**每一个** RSRWKV 块的空间混合器里，默认堆叠 $L=9$ 层（Table 2，第 9 页），不是网络里某个单独的全局打乱层。

**消融收益（Table 3，第 9 页）**：去掉 Random Shuffle，PSNR 从 42.0945 降到 41.9172（-0.1773dB），SSIM 从 0.9721 降到 0.9713，SAM 从 0.0214 升到 0.0224（变差），ERGAS 从 0.9081 升到 0.9274（变差）——四个指标一致变差，是完整、可对照的消融实验，不是孤立数字。

**作者是否给出"顺序对该任务不重要”的证据**：**不完全是**。作者给出的证据是"任何固定扫描顺序都会引入偏差，随机打乱后取期望（哪怕只采样一次，见 Fig. 9 的 $M$-扫描）能缓解这种偏差、提升指标”，这是"固定顺序有害、随机化有益”，而不是"顺序信息本身对预测无用”。这一区别很关键：随机打乱后模型仍然处理的是同一批 2D 空间 token（只是排列变了），任务的信息量没有损失，因为图像是**非因果、一次性完整可见**的，$T!$ 种排列在数学上描述的是同一个空间关系集合。

**能否搬到 2-IP 对内按时间排序的流序列上做顺序随机化消融**：可以做一个**离线诊断实验**，但不能直接搬用原文的"打乱—计算—逆打乱—蒙特卡洛平均”这套机制作为部署方案，原因是结构性的：
1. 时间顺序在流量场景里是真实因果语义（握手先后、突发节奏），不是像图像展平那样的任意标注顺序；打乱历史事件顺序会破坏这些语义，不是"等价重参数化”。
2. 在线检测系统在推断时刻无法访问未来事件去完成"打乱后再逆打乱”的闭环——图像任务的整张图在同一次前向传播内完整可见，而流序列是随时间到达的。
3. 可行的类比实验是**纯诊断性、离线**的：固定训练好的模型，在评价阶段把某个实体键（2-IP 对）已经观测到的历史事件顺序打乱后再计算因果前缀统计量，比较打乱前后下游指标（AP、召回）的变化——如果指标几乎不变，说明模型主要利用的是"过去事件的集合”而非"精细时间顺序”；如果指标明显下降，说明顺序编码了额外信号。这只能作为事后诊断，不能作为可部署的随机化训练/推断机制，也不能直接复用原文"$M=1$ 已经足够”的结论，因为二者的信息完整性前提不同。
