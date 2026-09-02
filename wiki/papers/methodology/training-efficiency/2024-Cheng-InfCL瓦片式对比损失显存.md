---
title: "Breaking the Memory Barrier: Near Infinite Batch Size Scaling for Contrastive Loss"
authors: [Zesen Cheng, Hang Zhang, Kehan Li, Sicong Leng, Zhiqiang Hu, Fei Wu, Deli Zhao, Xin Li, Lidong Bing]
year: 2024
date: 2026-09-02
journal: "arXiv:2410.17243（DAMO Academy, Alibaba Group；代码 DAMO-NLP-SG/Inf-CLIP）"
source_pdf: "[[raw/papers/methodology/training-efficiency/2024-Yuanhang-InfCL-Breaking-Memory-Barrier-Contrastive.pdf]]"
sha256: "678115a7c12f5419badd5385ed2e27a73625aef18fac9bc88371484fd2f4011e"
tags:
  - 瓦片计算
  - 对比损失
  - LogSumExp
  - 显存优化
  - 类型/论文
key_finding: "Inf-CL 针对的是对比损失里 O(b²) 相似度矩阵本身的显存瓶颈（不是编码器侧），用分块累积 LSE 把损失侧显存复杂度从 O(b²) 压到 O(b/n²)；论文声称的“no precision loss”是基于下游零样本分类/检索准确率在误差范围内一致的经验对照（Table 3、Table 4），全文检索 bitwise/round 零命中，不是逐位数值证明。"
method: "分块（tile-wise）前向累积 log-sum-exp + 跨 GPU 环形通信的粗粒度分块 + GPU 内 CUDA 核融合的细粒度分块（多级瓦片策略）"
baseline: "CLIP（vanilla 全矩阵实现）、OpenCLIP/DisCo-CLIP（局部损失，按 GPU 分片相似度矩阵）"
aliases:
  - Inf-CL
  - Inf-CLIP
  - Cheng2024-InfCL
---

# Inf-CL：瓦片式对比损失与近无限批量

> Cheng, Zhang, Li 等，2024，arXiv:2410.17243 · PDF 共 16 页

**本次核验范围**：第 1 页至第 16 页（全文，含摘要、§1–§6、参考文献、附录 A.1–A.3），使用 `pdf-converter`（`mineru-open-api flash-extract`，`--language en`，单次转换覆盖全部 16 页，未分页）。页码未逐页核对物理页面渲染，下文位置以论文自身的章节编号（§）为准；关键数字均标注表号或章节号。

## 一句话

Inf-CL 不解决编码器侧的显存问题（那是 GradCache 的范畴），而是解决对比损失计算本身——相似度矩阵 `X∈R^{b×b}` 及其 softmax/LSE——的 `O(b²)` 显存瓶颈，用"分块累积 log-sum-exp、多级瓦片"把损失侧显存降到线性甚至更低，代价是通信与核内串行计算的额外开销（论文报告与此前方法速度相当）。

## 背景：问题的演进（§1，第 1–2 页）

- 对比学习需要大批量提供充足负样本；批量增大后相似度矩阵 `X∈R^{b×b}` 的显存随 `b²` 增长，成为训练规模的硬瓶颈（§2.2，"Vanilla Implementation of Contrastive Loss"给出实测例子：ViT-B/16、批量 64k 时，模型本身只占 5.24GB，损失计算却要 66GB）。
- 既有方法各解决问题的一部分：GradCache（Gao et al., 2021）解耦模型和损失计算，但**损失本身的显存仍是瓶颈**（§1，"the memory cost of the loss still poses a significant bottleneck"）；OpenCLIP/DisCo-CLIP 把损失计算按 `n` 张 GPU 切分，显存降为 `1/n`，但仍是 `O(b²/n)`，多数研究止步于批量 128k。
- Inf-CL 的目标是把损失侧的显存复杂度从二次降到线性，理论上支持"近无限"批量。

## 方法核心

### 问题分解（§3.1，式 2）

把逐样本损失 `L_I = -1/b Σᵢ(xᵢᵢ - log Σⱼ exp(xᵢⱼ))` 拆成两部分：第一部分（正样本项）空间复杂度 `O(b)`，第二部分（log-sum-exp，LSE）才是 `O(b²)` 的根源。

### 分块前向（§3.1，式 3–5）

把相似度矩阵 `X` 按行列切成 `n_r × n_c` 个瓦片，对每个瓦片先算局部 LSE `l^{i,j}`（式 5，用行最大值做数值稳定化，防止指数溢出），再沿列方向串行合并成全局 LSE 向量 `l^i`（式 4，同样用 `log(1+exp(l^{i,j}-l^i))` 的数值稳定写法，逐瓦片增量更新）。这一合并过程本质是"在线 softmax/LSE"的增量算法，与 FlashAttention 一类分块 attention 算法同构。

### 分块反传（§3.1，式 6–8）与多级瓦片（§3.2）

- 反传同样只需要存储 `b` 维的 `l`（而非 `b×b` 的 `X`），用式 8 的增量累积重新算出 `∂L/∂I_i`。
- **跨 GPU 分块**（Algorithm 1）：每张 GPU 负责相似度矩阵的一部分行，用环形拓扑异步交换文本特征列，边通信边计算 LSE，把通信开销藏在计算时间里。
- **GPU 内分块**（Algorithm 2）：单卡内进一步按行分配给不同 CUDA 核，把逐行的迭代累积融合进一个 kernel，只在开始把特征从 HBM 读入 SRAM 一次、结束时把结果写回 HBM 一次，减少 HBM↔SRAM 的 I/O 次数（Figure 3）。
- 两级分块共同把复杂度做到：Vanilla `O(b²)` → 跨 GPU 分块 `O(b²/n²)` → 加上 GPU 内分块 `O(b/n²)`（Table 4 消融，§4.2）。

### “no precision loss”的论证层次（本次调研核心问题之一）

- **关键词检索结果**（全文，用 `rg -a -in 'bitwise|precision|\bround|\bfloat\b|floating|\bexact'`）：
  - `bitwise`：**0 次命中**。
  - `round`（词首）：**0 次命中**。
  - `precision`：**共 6 次命中**，逐一核对如下：
    1. §1 引言："Inf-CL maintains precision consistent with existing approaches"——一句概括性断言，未展开证明。
    2. Table 1 表注："Automatic Mixed Precision"——指训练用的混合精度（AMP），与本文方法的数值一致性无关。
    3. §4.1 实现细节："Automatic Mixed Precision (float16)"——同上，训练配置说明，非本文方法的精度论证。
    4. **§4.3 Performance Verification**（Table 3 附近）："our Inf-CL performs similarly to previous methods, with performance differences falling within the error margin, confirming that our design incurs no precision loss in the loss calculations"——**这是核心论证句**，依据是 Table 3 的零样本分类/检索准确率（ImageNet、ImageNet-v2、ObjectNet、ImageNet-OOD、MSCOCO R@1）在不同方法间的差异落在误差范围内。
    5. **§4.3 Ablation Study**（Table 4 附近）："we ablate multi-level tiling in Table 4 and show that our designs incur no precision loss in loss calculations. This allows arbitrary combinations to achieve nearly the same zero-shot classification accuracy (about 74.8% on ImageNet for 64k batch size)"——同样是下游准确率对照（Vanilla 74.82% vs OpenCLIP 74.86% vs 两级消融 74.78%/74.93%，见 Table 4 最后一列）。
    6. §5 相关工作末段："Increasing batch size improves the precision of gradient estimation"——这里"precision"指梯度估计的统计精度（估计量方差），与数值实现精度是完全不同的概念，不应混淆。
  - `float`（独立词）：**0 次命中**；`floating`：**0 次命中**（与 GradCache 不同，本文未出现"floating point(s)"这类存储单位表述）。
  - `exact`：**1 次命中**，出现在参考文献列表中 FlashAttention 论文的标题（"exact attention"），是引用文献题名的一部分，不是本文对自身方法的论断。
- **结论**：Inf-CL 的"no precision loss"是**经验准确率对照**——用不同实现在下游任务（零样本分类、图文检索）上的最终指标差异是否落在误差范围内来判断，属于统计意义上的"没有可观测的精度损失"，**不是**对分块 LSE 算法与全矩阵 LSE 算法在浮点算术上逐位等价的数值分析或证明。全文没有一处讨论浮点舍入、累加顺序或跨设备通信精度损失的具体机制。

## 实验结果

### 显存对比（Table 1，§4.2）

| 硬件 | 批量 | CLIP 峰值/损失 (GB) | OpenCLIP 峰值/损失 (GB) | Inf-CL 峰值/损失 (GB) |
| --- | --- | --- | --- | --- |
| 8×A800 | 32k | 46.40 / 16.67 | 43.97 / 2.27 | 44.20 / 0.18 |
| 8×A800 | 64k | 77.94 / 66.11 | 46.38 / 8.63 | 46.63 / 0.36 |
| 8×A800 | 128k | 超限（×） | 51.23 / 33.64 | 51.46 / 0.72 |
| 32×A800 | 128k | 超限（×） | 44.26 / 8.98 | 44.30 / 0.18 |

损失部分的显存差距在批量增大后急剧拉开（128k 时 OpenCLIP 33.64GB vs Inf-CL 0.72GB）。

### 最大可支持批量（Table 2，§4.2）

- ViT-B/16、8×A800：CLIP 68k、OpenCLIP 172k、Inf-CL 800k（提升 4.65×）；32×A800 提升到 9.60×。
- 结合"数据卸载"（data offload）策略后，ViT-L/14 在 8×A800 上可达 4096k 批量，32×A800 上可达 12288k（约 1228.8 万）。

### 训练速度（Figure 4，§4.2；Appendix A.2）

- 8×A800 上训练 ViT-L/14，一个 epoch 约 59 小时，与此前方法速度相当；批量从 64k 增到 256k，迭代时间近似线性增长约 4 倍（"220.3/49.4≈4"，§1）。
- Appendix A.2 给出速度未明显下降的两点原因：(1) 损失计算只占总迭代时间的很小一部分，尤其对大模型；(2) Inf-CL 把相似度矩阵计算和 softmax 融合进单次 SRAM↔HBM 通信，减少了 I/O 次数，部分抵消了分块串行带来的开销。

## 与本课题的关系

- **本课题推论（任务要求的适用性判断）**：Inf-CL 解决的是**损失侧** `O(b²)` 相似度矩阵的显存问题，其价值前提是相似度矩阵本身就大（论文实验批量在 32k–12288k 量级）。本课题第三章 BER 机制的排序批可达 6403 序列，但配对矩阵只有 `66×66`（约 4356 个元素），比论文最小实验批量 32k（约 10 亿元素级相似度矩阵）小七个数量级；损失侧显存在本课题中显然不是瓶颈——首步 OOM 的 30.97 GiB 主要来自编码器/序列处理侧的激活，而非一个 66×66 的相似度矩阵。因此 Inf-CL 的分块 LSE 技术对本课题第三章的排序损失**不构成直接可用的解法**，其价值更多是提供"分块累积 LSE 数值稳定写法"这一可迁移的实现技巧，而非显存优化本身。
- **可迁移机制**：式 4、式 5 的"分块 LSE 增量合并 + 逐块最大值稳定化"写法，是任何需要对大规模或分批数据做 softmax/LSE 归一化时的通用数值稳定技巧，可用于本课题任何涉及跨批次归一化的场景（若存在），但需独立验证数值稳定性，不能直接套用本文的显存复杂度结论。
- **不可直接声称**：不得引用本文的"no precision loss"支持"逐位一致"或"数值精确等价"的表述；本文的证据是下游任务准确率的经验对照，不是数值分析或逐位证明。也不得把本文的批量规模（32k 起步）与本课题的 66×66 配对矩阵类比为"同类问题的不同规模"，二者在本课题的语境下不是同一个瓶颈。
- **仍需实验验证的假设（本课题推论，论文未讨论）**：分块 LSE 的增量合并（式 4）本质是在线 softmax 算法，与全矩阵一次性 LSE 计算相比，浮点累加顺序不同，一般不保证逐位相同结果（这是在线 softmax/FlashAttention 类算法的普遍已知性质，但 Inf-CL 论文本身未做讨论、未给出数值误差界）；若本课题未来需要用到分块归一化技巧，其数值一致性需要独立设计最小实验验证，不能援引本文的经验准确率论证代替。

## 疑问 / 待验证

- 论文的准确率对照实验（Table 3、Table 4）都基于零样本分类和检索这类"下游任务指标"，指标本身对微小数值扰动不敏感（分类准确率是离散量），这种对照方式能检测出的精度差异粒度远粗于逐位数值分析，本课题若要做更严格的一致性论证需要更细粒度的指标（如直接比较损失值或梯度范数）。
- §4.3 提到极大批量（1024k）反而导致性能下降，论文将其归因于学习率/训练轮数等超参数未随批量调优（Appendix A.3），而非方法本身的缺陷；这一现象与本文数值精度论证无关，仅供批量规模趋势参考。

## 原始摘要

> Contrastive loss is a powerful approach for representation learning [...] we propose a tile-based computation strategy that partitions the contrastive loss calculation to arbitrary small blocks, avoiding full materialization of the similarity matrix. [...] it enables contrastive training of a CLIP-ViT-L/14 model with a batch size of 4M or 12M using 8 or 32 A800 80GB without sacrificing any accuracy.

## 文献信息

- arXiv: <https://arxiv.org/abs/2410.17243>
- 代码仓库：<https://github.com/DAMO-NLP-SG/Inf-CLIP>（论文正文给出的链接，未核验仓库内容与可复现性）
