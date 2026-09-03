---
title: "Reducing Activation Recomputation in Large Transformer Models"
authors: [Vijay Korthikanti, Jared Casper, Sangkug Lym, Lawrence McAfee, Michael Andersch, Mohammad Shoeybi, Bryan Catanzaro]
year: 2022
date: 2026-09-02
journal: "NVIDIA 技术报告，arXiv:2205.05198"
source_pdf: "[[raw/papers/methodology/training-efficiency/2022-Korthikanti-Reducing-Activation-Recomputation-NVIDIA.pdf]]"
sha256: "5fcd24e92a086f5671cbb8c0624cd42251d2d43324245da9d93b0b2289e46abc"
tags:
  - 训练效率
  - 激活重计算
  - 序列并行
  - 大模型训练
  - Transformer
  - 类型/论文
key_finding: "推导出逐层激活显存的解析表达式（第4节，式1–6，汇总于Table 2），据此提出序列并行（消除张量并行未切分区域的激活冗余）与选择性激活重计算（只重算大显存低FLOPs的注意力子块）；二者联用把激活显存降到基线的约20%（约5倍），把全量重计算原本30–40%的执行时间开销降到2–7%（第9–10页6.1、6.2节），在530B模型上把MFU从42.1%提到54.2%（Abstract）。"
method: "先推导单层激活显存的封闭解析式并逐一分析张量并行、序列并行、流水线并行对该式各项的影响（第4节）；再提出选择性激活重计算——只对Q,K,V之后、注意力核心部分（QK^T、softmax、softmax dropout、attention-over-V）做检查点重算，因为这部分显存占比高但每输入元素FLOPs低（第5节）；序列并行沿序列维度切分张量并行原本不切分的LayerNorm/Dropout区域，靠all-gather/reduce-scatter与张量并行的all-reduce带宽等价，不增加通信开销（第4.2.2节）。"
baseline: "无重计算（baseline，可能OOM）、全量激活重计算（full activation recomputation，标准做法）、仅张量并行不含序列并行"
aliases:
  - 序列并行
  - 选择性激活重计算
  - Selective Activation Recomputation
  - Korthikanti2022-激活重计算
related:
  - "[[2020-Jain-Checkmate最优张量重物化]]"
  - "[[2021-Kirisame-动态张量重物化]]"
---

# 减少大型 Transformer 模型的激活重计算

> Korthikanti, Casper, Lym, McAfee, Andersch, Shoeybi, Catanzaro（NVIDIA），2022，arXiv:2205.05198 · 17 页（正文 1–7 节 + 附录 A–C）

**本次核验范围**：全文 17/17 页完整核验，含正文第 1–7 节与附录 A（FLOPs 推导）、B（流水线并行显存优化）、C（微批级激活重计算，Appendix C）。未发现无法定位的章节。

## 一句话

本文先给出 Transformer 单层激活显存的解析表达式，再证明其中一大块（$5as/h$ 项，来自注意力 $QK^T$/softmax/dropout/attention-over-V）具有"显存占用大但每输入元素 FLOPs 很低"的特性，因此值得重点检查点重算；配合新提出的序列并行（消除张量并行遗留的激活冗余），两项技术联用把激活显存降低约 5 倍，把全量重计算带来的 30–40% 执行时间开销压到 2–7%，在 5300 亿参数模型上把 Model FLOPs Utilization 从 42.1% 提升到 54.2%（Abstract）。

## 背景：问题的演进

训练万亿参数级 Transformer 需要模型并行（张量并行+流水线并行）分摊参数与优化器状态，但流水线并行为压缩气泡需要缓存多个微批的激活，无法降低激活显存（第 1 节 Introduction）。标准应对方式是"全量激活重计算"（full activation recomputation）：只在每个 Transformer 层边界保存输入，反向时重算层内其余激活，但作者实测这带来 30–40% 的执行时间开销（第 1 节，第 2 段）。此前的序列并行提案（Li et al. 2021）要求参数和优化器状态在所有设备上复制，不适合大模型；Sagemaker（Karakus et al. 2021）、GSPMD（Xu et al. 2021）式的显存高效张量并行需要跨设备做 LayerNorm，通信/计算效率差（Sagemaker 每层 4 次 reduce-scatter，对比 Megatron-LM 张量并行每层仅 2 次 all-reduce）（第 2 节 Related Work）。本文的目标是不引入额外通信、计算或显存开销的前提下，把张量并行遗留的激活冗余也切分掉。

## 方法核心

- 单层激活显存解析式（第 4.1 节，式1）：在无模型并行时，
  $$\text{Activations memory per layer} = sbh\left(34+5\frac{as}{h}\right)$$
  其中 $s$ 序列长度、$b$ 微批大小、$h$ 隐藏维、$a$ 注意力头数。推导过程逐项列出注意力块（$11sbh+5as^2b$ 字节）、MLP 块（$19sbh$）、两个 layer-norm（$4sbh$）的显存来源（第 4.1 节正文，含每个子模块的详细显存拆解），$5as/h$ 项来自注意力核心（QK^T、softmax、softmax dropout、attention-over-V）。
- 张量并行下的显存式（第 4.2.1 节，式2）：
  $$sbh\left(10+\frac{24}{t}+5\frac{as}{ht}\right)$$
  其中 $t$ 是张量并行度；可见 $10sbh$ 这一部分（layer-norm 与 dropout 相关）**不随 $t$ 缩小**，因为张量并行不切分这些区域，这正是序列并行要解决的冗余来源。
- 序列并行（第 4.2.2 节，图5、图6，式3）：把张量并行未切分的区域（layer-norm、dropout）沿序列维度切分，引入新的通信算子 $g$/$\bar g$（分别是前向 all-gather+反向 reduce-scatter、前向 reduce-scatter+反向 all-gather），与原有张量并行的 $f$/$\bar f$ 算子（all-reduce）组合。作者证明：ring all-reduce 本身就是"reduce-scatter+all-gather"两步，因此序列并行与张量并行的通信带宽总量相同，**不引入额外通信开销**（第 4.2.2 节正文明确论证，"Therefore, sequence parallelism does not introduce any communication overhead"）。联用后单层激活显存式变为（式4）：
  $$\frac{sbh}{t}\left(34+5\frac{as}{h}\right)$$
  即原始式1整体除以 $t$。
- 流水线并行下的总激活显存（第 4.2.3 节，式5）：由于 1F1B 调度需要流水线第一阶段缓存 $p$ 个微批的激活（$p$ 为流水线并行度），第一阶段总显存为 $\frac{sbhL}{t}(34+5as/h)$（$L$ 为总层数），**不随 $p$ 均匀缩小**。
- 选择性激活重计算（第 5 节，图3红色虚线框）：核心判据——注意力核心部分（$QK^T$、softmax、softmax dropout、attention-over-V）"generally have large input sizes and thus large activations, however, the number of floating-point operations (FLOPs) per input element is very low"（第 5 节正文，这是选择"重算哪部分"的显式判据表述，位于本文提出选择性重计算方案的核心论证段落）。据此只检查点+重算这部分，保留其余部分（式6）：
  $$\text{Total required memory} = 34\frac{sbhL}{t}$$
  即把 $5as/h$ 这一项完全去掉（重算掉），只保留 $34$ 那部分。
  以 GPT-3（$a=96,s=2048,h=12288$，$5as/h=80$）与 MT-NLG（$a=128,s=2048,h=20480$，$5as/h=64$）为例，$5as/h$ 均大于 $34$，即注意力核心部分占激活显存的多数；据此选择性重计算可为 GPT-3、MT-NLG 分别节省 **70%、65%** 的激活显存，代价是仅增加 **2.7%、1.6%** 的 FLOPs 开销（第 5 节正文，Appendix A 给出 FLOPs 推导）。
- Table 2（第 6 页）汇总六种配置的单层激活显存公式：无并行 $sbh(34+5as/h)$；仅张量并行（基线）$sbh(10+24/t+5as/ht)$；张量+序列并行 $sbh(34/t)$（注：此处论文表格写法与式4等价）；张量并行+选择性重计算 $sbh(10+24/t)$；三者全用 $sbh(34/t)$；全量重计算 $sbh(2)$。

## 实验结果

- 显存节省（第 9 页 6.1 节，图7）：单独用序列并行或单独用选择性重计算都能把激活显存降到基线（仅张量并行）的约一半；两者联用把显存降到基线的**不到 20%**（约 5 倍缩减），仅比全量重计算（10%）多约 2 倍，但换来的是执行时间几乎不受影响。
- 单层执行时间分解（第 9 页 6.2 节，Table 4，22B 模型）：无重计算基线前向 7.7ms/反向 11.9ms/合计 19.6ms；仅序列并行几乎不增加显存但把合计降到 19.0ms（-3%，因 layer-norm/dropout 只处理 $1/t$ 数据）；全量重计算合计 27.2ms（**+39% 开销**，反向从 11.9ms 增至 19.5ms）；仅选择性重计算合计 20.9ms（**+7% 开销**，反向增至 13.2ms，多出的 1.3ms 仅为全量重计算多出的 7.6ms 的约六分之一）；序列并行+选择性重计算合计 20.3ms（**+4% 开销**）。
- 随模型规模的趋势（第 10 页图8）：模型越大，选择性重计算相对全量重计算的开销优势越明显——530B 与 1T 模型上选择性重计算+序列并行开销仅 2%，对比全量重计算 36%。
- 端到端迭代时间（第 10 页 6.3 节，Table 5）：22B/175B/530B/1T 四档模型，本文方法相对全量重计算（无序列并行）的吞吐提升分别为 29.0%/31.8%/29.7%/32.1%；1T 模型 MFU 达到 56.3%、HFU 达到 57.0%；530B 模型扩展到 8 路数据并行（2240 GPU）后 MFU 从 56.0% 降至 54.2%（Abstract 中的 54.2% 即此数字，对应"比 42.1% 快 29%"这一 Abstract 表述——42.1% 是原全量重计算方案在同等配置下的 MFU）。
- FLOPs 硬件/模型比（第 10 页 6.3 节末段；Appendix A 式9）：本文方法下硬件 FLOPs 与模型 FLOPs 之比约为 $1+s/6h$，非常接近 1，说明选择性重计算引入的额外计算量极小。

## 我的理解

这篇论文的核心贡献是把"要不要重计算"这个二元问题拆成了两个正交维度：一是从源头**消除冗余**（序列并行——张量并行本来就没切分的部分，切了不增加通信代价，纯收益）；二是在无法避免的重计算里**挑最划算的部分**重算（选择性重计算——挑显存大但 FLOPs 密度低的算子，这样"花小算力换大显存"）。这两步分开来看都不新颖（序列切分、部分重算前人都做过类似尝试），但本文把它们量化到一个统一的解析显存公式里（式1–6，Table 2），使得"该不该重算、重算哪部分"从工程直觉变成了可以直接代入模型超参数计算的判据，这是其相对此前经验性重计算方案的关键区别。

## 与本课题（BER 训练效率／第四章候选）的关系

### 论文原结论
- **逐层激活显存的解析表达式**位于第 4 节（正文第 4.1–4.3 节，式1–6），Table 2（第 6 页）汇总六种配置的公式，全部为精确推导（作者说明只忽略了远小于主项的次要项，如 layer-norm 的均值方差存储，第 4 节开头有明确近似说明）。
- **"按显存占用大但重算 FLOPs 小来选算子"这一判据的原文位置**：第 5 节正文（对应本文提取稿第 181 行前后），原文原话是"These operations generally have large input sizes and thus large activations, however, the number of floating-point operations (FLOPs) per input element is very low."，紧接着的判据总结句是"for large models where $5as/h>34$, if we checkpoint and recompute this part of the transformer layer, we store less than half of the activations and only have a modest cost to recompute those that aren't stored."
- **全量重计算的时间开销**：Introduction 中的整体估计为 30–40%（第 1 节第 2 段）；Table 4 中单层的精确实测为 39%（合计时间）/64%（反向时间单独看）；随模型规模变化的趋势见图8，530B/1T 模型上全量重计算开销为 36%。
- **选择性重计算省下的显存百分比与付出的 FLOPs 百分比**：GPT-3 省 70% 显存代价 2.7% FLOPs；MT-NLG 省 65% 显存代价 1.6% FLOPs（第 5 节正文，明确数字）。
- **"在显存允许范围内尽量多保存若干微批激活、其余重算"这一做法的原文评价**（Appendix C，微批级激活重计算/Microbatch Level Activation Recomputation）：原文明确评价为"增量收益较小"——在已经应用序列并行+选择性重计算的基线上，该技术把 175B 与 530B 模型的 MFU 分别再提升 **+0.7%**（到 52.3%）与 **+0.4%**（到 56.4%）（第 17 页 Appendix C 末段）。原文对此增益给出的归因是"the gain is small because the selective recomputation overhead is as small as ∼2%"，即因为选择性重计算本身已经把重算开销压得很低，进一步"少重算几个微批"的边际收益自然有限；但作者同时给出了正面的适用边界提示——"one can imagine model parallel configurations where there is nearly enough memory for no recomputation, in which case microbatch level activation recomputation could provide more improvement to training speed"，即在显存接近"几乎不需要重计算"的临界配置下，这一技术会有更大价值。**这是原文对候选四 SAC 思路最直接的对照评价：不是负面结论，而是"在本文测试的配置下收益小，但在特定显存临界区间可能收益更大"的条件性评价，且原文只字未提"计算量上限倍数"这类判据，是候选四自评的 4M/3M=1.33 倍与本文场景不同的量化口径。**

### 本课题推论（原文未给出，本课题基于原文外推）
- 本文的显存解析式（式1–6）是针对标准 Transformer 编码器/解码器结构（自注意力+MLP+两个 layer-norm）推导的，BER 排序头若结构不同（例如引入了非标准的 CVaR-pAUC 聚合算子），不能直接代入本文公式估算显存构成，需要针对 BER 实际结构重新做逐算子显存拆解——此为本课题推论，原文未涉及非标准排序损失结构。
- 若要把本文"选择显存大、FLOPs 密度低的算子做检查点重算"这一判据迁移到候选四 SAC 或候选一 ASB 的算子选择逻辑上，需要先对 BER 排序头做逐算子的显存/FLOPs profile，确认是否存在类似 $QK^T$/softmax 这样"贵显存、廉算力"的子模块——此为本课题推论，需要独立的 profile 实验支持。

### 可迁移机制
- "先建立逐算子/逐层的显存-FLOPs 解析或经验模型，再据此选择重算对象"这一方法论（而非具体的 $34+5as/h$ 公式本身，该公式专属标准 Transformer 层结构）是可迁移的通用范式，可直接指导候选四 SAC 或候选一 ASB 在 BER 排序头上做算子级/微批级选择依据的构建。
- 序列并行"消除模型并行未覆盖区域的激活冗余、且不增加通信开销"这一设计原则，对本课题若未来引入张量并行等模型并行手段时具有参考价值，但当前 BER 训练未见使用张量并行，暂不构成直接可用机制。

### 不可直接声称的内容
- 不能声称候选四 SAC 的"保留 k 个微批不重算"思路已被本文验证为显著有效——本文 Appendix C 的实测结果恰恰是"增量收益小"（+0.7%、+0.4% MFU），且是在已经应用了序列并行与选择性重计算这两项更大收益手段之后的锦上添花效果，并非独立于这两项技术的单独收益评估。若候选四打算脱离序列并行/选择性重计算的语境单独评估"保留部分微批"的收益，不能直接引用本文数字，因为量化配置不同（本文的收益基准已经很低的重算开销之上）。
- 不能声称本文的 5 倍显存缩减、2–7% 时间开销等数字可直接套用于 BER 场景——这些数字高度依赖标准 Transformer 层的具体结构比例（$5as/h$ vs $34$ 的相对大小），BER 排序头的结构比例未知，需要独立 profile。

### 仍需实验验证的假设
- BER 排序头是否存在类似"$5as/h$ 项"这样显存占比高但 FLOPs 密度低的子结构，若存在，选择性重计算该部分能否取得类似本文的显存/时间权衡——待验证。
- 候选四 SAC 的"保留 k 个微批"思路，在 BER 训练实际的显存临界配置下（当前实测排序批次 6403 序列、激活需 30.97 GiB 逼近 GPU 可用 31.36 GiB 的场景），是否落在本文 Appendix C 提示的"显存接近无需重算的临界区间"（该区间下微批级技术收益更大）——待验证，需要结合 BER 实际显存余量数据判断。

## 与相关工作的关系

本文与 ZeRO/ZeRO-Offload/ZeRO-Infinity（Rajbhandari et al. 2020/2021）、DeepSpeed（Rasley et al. 2020）等数据并行式显存优化方案是互补而非竞争关系，本文明确声明"专注于模型并行优化"、"对比数据并行式技术的分析超出本文范围"（第 2 节 Related Work 末段）。与 Megatron-LM 张量并行（Shoeybi et al. 2019）是直接的基础依赖关系（本文的序列并行是在其之上的扩展）。与 [[2020-Jain-Checkmate最优张量重物化]]、[[2021-Kirisame-动态张量重物化]] 的关系是互补：后两者解决通用的"给定计算图，哪些张量该重算"的调度问题，本文解决"Transformer 特定结构下如何从源头减少激活总量（序列并行）与如何挑选性价比最高的重算对象（选择性重计算）"，是针对特定架构的领域知识优化，理论上可与 Checkmate/DTR 式通用调度器叠加使用，但本文未做此类叠加实验。

## 疑问 / 待验证

- 本文全部实验基于 Megatron-LM/NeMo-Megatron 框架下的标准 GPT 式 Transformer，未涉及排序损失、对比学习损失或本课题的 CVaR-pAUC 多预算损失结构，迁移前需要独立验证适用性。
- Appendix C 的微批级技术只在 175B、530B 两档模型上报告了 MFU 提升数字，22B 与 1T 两档未见对应数字，原文未说明是否因这两档不适用或未测试。

## 原始摘要

> Training large transformer models is one of the most important computational challenges of modern AI. In this paper, we show how to significantly accelerate training of large transformer models by reducing activation recomputation. Activation recomputation is commonly used to work around memory capacity constraints. Rather than storing activations for backpropagation, they are traditionally recomputed, which saves memory but adds redundant compute. In this work, we show most of this redundant compute is unnecessary because we can reduce memory consumption sufficiently without it. We present two novel yet very simple techniques: sequence parallelism and selective activation recomputation. In conjunction with tensor parallelism, these techniques almost eliminate the need to recompute activations. We evaluate our approach on language models up to one trillion parameters in scale and show that our method reduces activation memory by 5×, while reducing execution time overhead from activation recomputation by over 90%. For example, when training a 530B parameter GPT-3 style model on 2240 NVIDIA A100 GPUs, we achieve a Model Flops Utilization of 54.2%, which is 29% faster than the 42.1% we achieve using recomputation.

## 文献信息

- arXiv:2205.05198（NVIDIA 技术报告）
- 原件：`raw/papers/methodology/training-efficiency/2022-Korthikanti-Reducing-Activation-Recomputation-NVIDIA.pdf`
- 实现：Megatron-LM 与 NeMo-Megatron（第 1 页摘要末尾）
