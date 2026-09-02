---
title: "Dynamic Tensor Rematerialization"
authors: [Marisa Kirisame, Steven Lyubomirsky, Altan Haan, Jennifer Brennan, Mike He, Jared Roesch, Tianqi Chen, Zachary Tatlock]
year: 2021
date: 2026-09-02
journal: "ICLR 2021，arXiv:2006.09616"
source_pdf: "[[raw/papers/methodology/training-efficiency/2021-Kirisame-Dynamic-Tensor-Rematerialization-ICLR.pdf]]"
sha256: "a3b6b6d229a1b21b9c67aee2cb17612837796ca192f79d8741509b752ba0a8b2"
tags:
  - 训练效率
  - 激活重计算
  - 在线算法
  - 贪心启发式
  - 动态计算图
  - 类型/论文
key_finding: "DTR 是一个运行时驱动的在线贪心重物化算法，用启发式分数 h_DTR(t)=c(t)/[m(t)·s(t)]（代价/(显存×陈旧度)）动态决定驱逐哪个张量；证明在 N 层线性前馈网络、Ω(√N) 显存预算下只需 O(N) 张量操作，与离线静态方案同阶（Theorem 3.1，第4页），但也证明任意确定性启发式在最坏情况下会比离线最优多做 Ω(N/B) 次计算（Theorem 3.2，第4页）；在模拟实验中其近似 h_DTR^eq 与 Checkmate 的最优解性能接近（第6页图3）。"
method: "运行时拦截张量的分配、访问、释放事件；显存不足时按启发式分数驱逐张量，需要时通过重放生成该张量的父算子来重物化（可递归）；核心启发式综合三个逐张量的元数据：陈旧度 s(t)、显存占用 m(t)、以及把该张量及其驱逐邻域重新计算所需的投影代价 c(t)。"
baseline: "Checkmate（Jain et al. 2020，离线 ILP 最优解）、Chen et al. (2016) 静态 sqrt(n)/log(n) 检查点方案、Capuchin (Peng et al. 2020) 的 MSPS 启发式、GreedyRemat (Kumar et al. 2019)、LRU、随机基线"
aliases:
  - DTR
  - Dynamic Tensor Rematerialization
  - Kirisame2021-动态张量重物化
related:
  - "[[2020-Jain-Checkmate最优张量重物化]]"
  - "[[2022-Korthikanti-大规模Transformer激活重计算优化]]"
---

# 动态张量重物化

> Kirisame, Lyubomirsky, Haan, Brennan, He, Roesch, Chen, Tatlock，2021，ICLR 2021 · arXiv:2006.09616 · 31 页（正文 1–7 节 + 附录 A–E）

**本次核验范围**：全文 31/31 页均已提取；正文第 1–7 节（含 3 formal bounds 的完整证明推导过程）与附录 A（Theorem 3.1 证明）、D.2/D.3（消融研究中的驱逐策略对比、运行时开销）、E.1–E.3（PyTorch 原型实现细节）逐段核验；附录 B（Theorem 3.2 证明）、C.1–C.4（模拟器形式化定义细节）仅核对了标题与所在位置，未逐条核验其内部数学推导，本笔记中凡引用这两部分之外的内容均已核验原文页码/小节。

## 一句话

DTR 把重物化从"训练前静态规划"改造成"运行时按需驱逐/重放"的在线贪心算法：它像一个张量级缓存，用综合陈旧度、显存占用与重算代价的启发式分数动态决定驱逐谁，不需要提前知道计算图结构，因此天然支持动态控制流模型；理论上在线性前馈网络上能匹配离线最优的渐进复杂度（$O(N)$，$\Omega(\sqrt N)$ 显存），但作者也证明了在线算法无法在所有网络结构上都匹配离线最优（存在对抗网络使在线算法多做 $\Omega(N/B)$ 倍计算）。

## 背景：问题的演进

已有的 DL 检查点技术（Chen et al. 2016、Jain et al. 2020 即 Checkmate、Kumar et al. 2019、Gruslys et al. 2016）都在训练前对**静态计算图**做离线规划（第 1 节 Introduction）。这一前提在动态模型（如 TreeLSTM 这类数据依赖控制流的模型）上失效或代价高昂——要么需要"展开"动态图对每种输入分别规划，要么规划本身开销过大无法逐 epoch 重跑。本文提出：静态离线规划对 DL 检查点场景并非必需，一个足够简单的在线算法就能取得可比的性能（第 1 节，本文核心论点）。

## 方法核心

- 运行时设计（第 2 节，图 1）：拦截张量分配（`AllocateBuffer`）、访问、释放三类事件。分配时若显存不足，按启发式驱逐已驻留张量直至腾出空间；访问已驱逐张量时通过重放其父算子重物化（若父算子的输入也被驱逐则递归重物化）；释放时更新元数据并可主动做"有利可图"的驱逐。
- 核心启发式（第 2 节，正文公式，第 4 页）：
  $$h_{\mathrm{DTR}}(t) = \frac{c_0(t)+\sum_{t'\in e^*(t)} c_0(t')}{m(t)\cdot s(t)}$$
  其中 $s(t)$ 是自上次访问以来的时间（陈旧度）、$m(t)$ 是张量大小、$c_0(t)$ 是从父张量重算 $t$ 的耗时；$e^*(t)$ 是 $t$ 的"驱逐邻域"——需要被重物化才能算出 $t$、或需要 $t$ 才能被重物化的已驱逐张量集合。分数越小越先被驱逐（最陈旧、最大、重算最省的张量优先驱逐）。
- 近似启发式 $h_{\mathrm{DTR}}^{\mathrm{eq}}$（第 2 节；正文公式，第 4 页）：用无向松弛（union-find 结构，支持近常数时间合并但不支持精确拆分）近似 $e^*$，在实验中性能与 $h_{\mathrm{DTR}}$ 相近，但元数据访问次数最多减少两个数量级（第 4.2 节，附录 D.3）。
- 消除策略（第 2 节"Deallocation"段）：论文比较了忽略释放事件、驱逐已释放张量、"banishing"（永久释放，唯一能释放常量张量的方式，但会阻止其子张量未来被重物化）三种策略；正文最终选用"eager eviction"（一有外部引用释放就立刻驱逐）作为主实现（详细对比见附录 D.2）。
- 形式化理论边界（第 3 节）：
  - Theorem 3.1（第 4 页，简化启发式 $h_{e^*}$）：$N$ 层线性前馈网络、显存预算 $B=\Omega(\sqrt N)$ 下，DTR 可用 $O(N)$ 张量操作完成一次前向+反向，与 Chen et al. (2016) 的离线静态方案同阶。证明思路（附录 A）：前向阶段无重算，恰好 $N$ 次操作；启发式确保前向结束时驻留的 $B$ 个张量近似均匀分布（间隔 $L\le 2(N-2)/(B-1)$，Lemma A.1）；反向阶段随着梯度算完、检查点被"banish"，可用空间递增，重算代价按 $O(L_k+L_k^2\log k/k^2)$ 递减求和，总代价收敛到 $O(N)$。
  - Theorem 3.2（第 4 页，附录 B 证明概要）：对任意确定性启发式 $h$，存在一个由 $B$ 条线性前馈子网络共享一个父张量组成的对抗图，使 DTR 在预算 $B\le N$ 下需要 $\Omega(N/B)$ 倍于离线最优的张量操作——因为在线算法无法重排计算顺序，可被诱导反复重算整条已被驱逐的路径。
- 原型实现（第 5 节）：仅用 1,161 行核心代码 + 2,647 行样板 operator overload 集成进 PyTorch，主要通过拦截张量分配与算子调度，无需深改 PyTorch 内存管理内部机制（第 5 节正文）。

## 实验结果

- 模拟实验跨启发式比较（第 4.2 节，图 2）：在 ResNet-1202、Transformer、UNet、TreeLSTM、LSTM、Unrolled GAN 等静态+动态模型上，纳入更多信息的启发式（$h_{\mathrm{DTR}}$、$h_{\mathrm{DTR}}^{\mathrm{eq}}$、$h_{\mathrm{MSPS}}$）能在更低显存预算下运行且重物化次数更少，但运行时开销也更高——$h_{\mathrm{DTR}}$ 比 $h_{\mathrm{DTR}}^{\mathrm{eq}}$ 多出最多两个数量级的元数据访问，比 $h_{\mathrm{DTR}}^{\mathrm{local}}$ 多出最多三个数量级（第 4.2 节末段，附录 D.3 详细数据）。即使是最简单的 $h_{\mathrm{LRU}}$，通常也能在减少 30% 显存下完成训练。
- 与 Checkmate 对比（第 5 页 4.3 节，图 3）：DTR 的 $h_{\mathrm{DTR}}$ 与 $h_{\mathrm{DTR}}^{\mathrm{eq}}$ 启发式取得的性能"remarkably close to Checkmate's optimal solutions"；即使更简单的 $h_{\mathrm{LRU}}$ 也优于静态基线。差异在于：Checkmate 需要完整的提前模型知识，每个预算求解需要数秒到数分钟的 ILP 求解；DTR 无需提前知识，毫秒级动态找到可比方案。
- 原型实测（第 5 节，图 4、Table 1）：ResNet-1202 上 PyTorch 原生最大可训 batch size 64，DTR 支持到 140；Transformer 从 30 提升到 90；UNet 从 7 提升到 10；TreeLSTM（动态模型）从 $2^6-1$ 节点提升到 $2^9-1$ 节点，验证了 DTR 对动态控制流模型的原生支持（这是静态离线方法难以做到的）。
- 消融：驱逐策略对比（附录 D.2，图 11）：banishing（永久释放）在多数模型上能达到的最低预算不如 eager eviction，UNet 上差距明显（banishing 只能支持基线预算的 90%，eager eviction 能支持到 50%）；但 banishing 在 ResNet 上以相同预算取得更低的计算开销。两者都明显优于"忽略释放"策略，说明释放事件本身携带有用信息。
- 消融：元数据来源（附录 D.1，图 7–10）：更精确的驱逐邻域度量（$c=e^*$）总能带来更多显存节省；陈旧度 $s$ 与大小 $m$ 的重要性因模型架构而异——静态模型（DenseNet、ResNet、UNet）上单用代价+大小已经很好，动态模型上加入陈旧度更重要。

## 我的理解

DTR 与 Checkmate 的关系本质是"在线贪心 vs 离线最优"这一经典系统设计权衡的具体实例：Checkmate 拿到完整计算图后一次性求解全局最优（数秒到一小时），DTR 不需要提前知道图结构、边运行边决策（毫秒级），代价是理论上存在被对抗构造出的最坏情况（Theorem 3.2），且实践中启发式的信息量与运行时开销成正比（更精确的 $e^*$ 更贵）。论文最有说服力的证据不是"DTR 比 Checkmate 好"，而是"DTR 几乎不比 Checkmate 差，同时多出了对动态模型的原生支持"——这是一个典型的"用可接受的性能损失换取适用范围扩大"的系统论文论证结构。

## 与本课题（BER 训练效率／第四章候选）的关系

### 论文原结论
- DTR 是运行时张量级缓存策略，决策粒度是**单个张量**，驱逐与重物化都在训练过程中动态发生，不依赖训练前对计算图的静态分析。
- Theorem 3.2 明确证明：**不存在能在所有网络结构上都匹配离线最优的确定性在线启发式**——这是一个有严格证明的负结果，不是经验观察。
- 论文的全部理论保证（Theorem 3.1）局限于线性前馈网络这一简化设定；对一般 DAG（如带残差连接的真实网络）只有实验验证（第 4 节模拟结果），没有对应的复杂度证明。

### 本课题推论（原文未给出，本课题基于原文外推）
- BER 排序头目前用的 `torch.utils.checkpoint` 是训练前手工指定的静态检查点划分（相当于本文语境下的"最粗粒度静态方案"），既不是 DTR 式的运行时动态决策，也不是 Checkmate 式的离线最优规划。若候选四 SAC 想借鉴 DTR 的"运行时按启发式动态决定保留哪些微批的激活"，需要把 DTR 的张量级驱逐逻辑重新设计为微批级决策——这是本课题需要独立验证的适配工作，原文的启发式（陈旧度、大小、驱逐邻域代价）是为逐张量场景设计的，微批粒度下"陈旧度"这一概念是否仍有意义、如何定义，原文未涉及。
- Theorem 3.2 的负结果提示：即便候选四设计出一个"运行时动态选保留哪些微批"的在线启发式，也不能默认它总能匹配离线最优（如穷举搜索或 Checkmate 式 MILP 求解的最优微批选择）；是否存在类似对抗结构（会诱导在线算法反复付出额外代价的微批排列）需要针对 BER 训练时的具体微批访问模式单独分析，本条纯属本课题推论。

### 可迁移机制
- "用陈旧度×大小×重算代价三个可运行时低成本获取的元数据构造驱逐分数"这一设计模式具有一般性，可作为候选四设计微批级驱逐启发式时的参考起点（元数据从张量替换为微批的对应量：微批上次被访问的时间、微批激活总显存、重新计算该微批前向的耗时）。
- "用近似邻域（union-find 式松弛）换取运行时开销降低，同时用实验验证近似不显著损失效果"这一权衡策略（$h_{\mathrm{DTR}}^{\mathrm{eq}}$ vs $h_{\mathrm{DTR}}$）可迁移：若微批级驱逐邻域的精确计算开销过大，可以类比设计一个近似版本并做同样的"精度-开销"消融。

### 不可直接声称的内容
- 不能声称 DTR 的 $O(N)$ 复杂度保证（Theorem 3.1）适用于任意网络结构——该定理的证明严格依赖线性前馈网络这一简化假设，本文自己也用 Theorem 3.2 证明了一般情形下在线算法可能远劣于离线最优。
- 不能声称 DTR 在 Transformer 或本课题的排序损失结构上有专门验证的性能数字——原文 Table 1 的 Transformer 实验是通用 Transformer 编码器基准（序列长度 256），未涉及 CVaR-pAUC 排序损失或多预算实体排序场景。

### 仍需实验验证的假设
- 把 DTR 式在线驱逐启发式改造为微批粒度、应用于 BER 排序头的激活管理，能否在不引入 Theorem 3.2 式最坏情况的前提下取得优于当前静态 `torch.utils.checkpoint` 方案的显存-速度权衡——待验证。
- $h_{\mathrm{DTR}}^{\mathrm{eq}}$ 式近似邻域松弛在微批粒度下是否仍能保持"性能接近精确版本、开销显著降低"这一权衡——待验证。

## 与相关工作的关系

本文与 [[2020-Jain-Checkmate最优张量重物化]] 构成核心对照，第 4.3 节图 3 直接复用并扩展了 Checkmate 论文的实验（作者在附录/致谢中特别感谢 Checkmate 作者协助搭建对比实验）；与 Capuchin (Peng et al. 2020)、Superneurons (Wang et al. 2018) 同属"运行时系统结合检查点/换出"的谱系（第 6 节 Related Work），区别在于 Capuchin 和 Superneurons 仍假设静态模型结构（通过初始 profiling batch 推断），只有 DTR 完全不依赖静态结构假设。与 [[2022-Korthikanti-大规模Transformer激活重计算优化]] 的关系是互补：DTR 解决"运行时如何决定驱逐哪个张量"的通用调度问题，NVIDIA 论文解决"Transformer 特定结构下如何从源头减少需要保存的激活总量"（序列并行）与"哪类激活值得选择性重算"，二者作用层面不同。

## 疑问 / 待验证

- Theorem 3.2 的对抗网络构造（附录 B）本笔记未逐行核验其数学细节，只核对了定理陈述与证明思路概述（第 4 页正文），完整证明的严谨性未经本次阅读独立验证。
- 附录 C.1–C.4（模拟器的形式化定义）本笔记仅核对标题与位置，未核验其内部具体定义与本文正文中启发式公式的一致性，如需引用模拟器内部细节应重新核验。

## 原始摘要

> Checkpointing enables the training of deep learning models under restricted memory budgets by freeing intermediate activations from memory and recomputing them on demand. Current checkpointing techniques statically plan these recomputations offline and assume static computation graphs. We demonstrate that a simple online algorithm can achieve comparable performance by introducing Dynamic Tensor Rematerialization (DTR), a greedy online algorithm for checkpointing that is extensible and general, is parameterized by eviction policy, and supports dynamic models. We prove that DTR can train an N-layer linear feedforward network on an Ω(√N) memory budget with only O(N) tensor operations. DTR closely matches the performance of optimal static checkpointing in simulated experiments. We incorporate a DTR prototype into PyTorch merely by interposing on tensor allocations and operator calls and collecting lightweight metadata on tensors.

## 文献信息

- ICLR 2021；arXiv:2006.09616
- 原件：`raw/papers/methodology/training-efficiency/2021-Kirisame-Dynamic-Tensor-Rematerialization-ICLR.pdf`
