---
title: "SAINT: Improved Neural Networks for Tabular Data via Row Attention and Contrastive Pre-Training"
authors: [Gowthami Somepalli, Micah Goldblum, Avi Schwarzschild, C. Bayan Bruss, Tom Goldstein]
year: 2021
date: 2026-08-28
journal: "arXiv:2106.01342v1 [cs.LG]，2021 年 6 月 2 日，18 页，首页标注 Preprint. Under review"
source_pdf: "[[raw/papers/methodology/2021-Somepalli-SAINT-Row-Attention-Tabular.pdf]]"
sha256: "9069de09bcd867b6b8604460f5d98de678eef5a731fac0e2a4216fa850aad018"
arxiv_id: "2106.01342v1"
tags:
  - 表格数据
  - Transformer
  - 行间注意力
  - 对比学习
  - 自监督预训练
  - 类型/论文
key_finding: "SAINT 在自注意力块之后加入跨样本的行间注意力块（第4页，3.2节，式2；算法1，第5页），在14个二分类+2个多分类公开表格数据集上5次试验平均AUROC达93.13%，超过XGBoost（91.06%）、LightGBM（90.13%）、CatBoost（90.73%）等提升树基线（第7页，表2）。"
method: "对类别与连续特征统一投影到d维嵌入空间并拼接[CLS] token；每个stage先做样本内自注意力，再把整批b个样本的拼接特征向量当作长度b的序列做行间注意力（跨样本自注意力）；配合CutMix+mixup生成的视图做对比学习与去噪联合损失的半监督预训练"
baseline: "Logistic Regression、Random Forest、XGBoost、LightGBM、CatBoost、MLP、VIME、TabNet、TabTransformer"
aliases:
  - Somepalli2021-SAINT
  - SAINT行间注意力
related:
  - "[[2025-Gorishniy-TabM参数高效集成]]"
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
---

# SAINT：行间注意力与对比预训练改进表格神经网络

> Somepalli, Goldblum, Schwarzschild, Bruss, Goldstein，2021，arXiv:2106.01342v1 · 18 页

## 一句话

SAINT 在标准 Transformer 编码器的样本内自注意力之后，额外插入一个把整批样本当作"序列"做自注意力的行间注意力块，使每一行的表征可以借用同一训练批次内其他行的信息；配合对连续特征也做逐列嵌入与对比+去噪自监督预训练，在16个公开表格基准上平均超过多种提升树方法。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：SAINT: Improved Neural Networks for Tabular Data via Row Attention and Contrastive Pre-Training
- arXiv：2106.01342v1 [cs.LG]，2021 年 6 月 2 日（第 1 页左侧竖排标记）
- 状态：首页页脚标注 "Preprint. Under review"（第 1 页），未标注正式会议/期刊版式
- 原件：`raw/papers/methodology/2021-Somepalli-SAINT-Row-Attention-Tabular.pdf`

## 论文原结论

### 架构与行间注意力机制

- 数据编码（第 3–4 页）：每个样本 xi 前置一个可学习 [CLS] token；n 个类别/连续特征各自经独立嵌入函数 E 投影到 d 维空间。与 TabTransformer 只嵌入类别特征不同，SAINT 对每个连续特征也单独用一个带 ReLU 的单层全连接层投影到 d 维（第 4 页，"Encoding the Data"），5.1 节的消融证实这一改动本身就能显著提升性能（见下）。
- 单个 stage 两步走（第 3–4 页，3.1 节，式 1–2）：先是样本内多头自注意力块（MSA，对同一行的 n+1 个 token 做标准 Transformer 编码器），再是行间注意力块（MISA）。公式：
  - 自注意力：`z_i^(1)=LN(MSA(E(x_i)))+E(x_i)`，`z_i^(2)=LN(FF1(z_i^(1)))+z_i^(1)`（第 4 页，式 1）
  - 行间注意力：`z_i^(3)=LN(MISA({z_i^(2)}_{i=1}^b))+z_i^(2)`，`r_i=LN(FF2(z_i^(3)))+z_i^(3)`（第 4 页，式 2），注意 MISA 的输入是**整个 batch 的集合** `{z_i}_{i=1}^b`，而不是单个样本。
- 行间注意力的具体实现（第 4–5 页，3.2 节 + 算法 1 + 图 2）：把单个样本的全部特征嵌入沿特征维拼接成一个 n·d 维长向量；把一个 batch 内 b 个样本的长向量堆成"长度为 b"的序列；对这个长度 b 的序列做标准多头自注意力（此时"token"是整行样本，而非单个特征）；再 reshape 回 (b,n,d)。算法 1 伪代码（第 5 页）：`x = reshape(x,(1,b,n*d))` → `self_attention(x)`（内部 `attn = softmax(qk^T/√d)`，形状 1×b×b）→ reshape 回 (b,n,d)。
- 与 Axial Attention / MSA Transformer / TABBIE 等行列注意力先例的区别（第 2 页，"Related Work—Axial Attention"）：那些工作里"同一数据点的不同特征互相通信，并与整批数据中相同特征位置通信"；而 SAINT 的行间注意力是"分层"的——先让同一数据点内部特征互相交互，再让不同数据点用**整行**互相交互（原文："first features of a given data point interact with each other, then data points interact with each other using entire rows/samples"，第 2 页）。作者把该机制类比为"完全图上的 GAT，所有表格行两两相连"（第 3 页）。

### 关键数字（含页码/表号）

- 主结果（第 7 页，表 2，14 个二分类数据集 + 2 个多分类数据集，5 次试验均值 AUROC）：SAINT 93.13%，SAINT-i 93.09%，SAINT-s 92.59%；对比 XGBoost 91.06%、LightGBM 90.13%、CatBoost 90.73%、TabTransformer 90.86%。"在 16 个数据集中的 13 个上，某个 SAINT 变体超过全部基线"（第 7 页，5.1 节）。
- 架构成本对比（第 6 页，表 1，14 个数据集均值，batch=32，100 epoch 训练+推理耗时）：SAINT-s（仅自注意力，L=6，h=8）91.6M 参数 / 1759 秒；SAINT-i（仅行间注意力，L=1，h=8）352.7M 参数 / 123 秒；SAINT（both，L=1，h=8）347.3M 参数 / 144 秒。行间注意力变体参数量远高于纯自注意力变体，但训练+推理反而快得多。
- 连续特征嵌入消融（第 8 页，5.1 节）：原版 TabTransformer 平均 AUROC 89.38；仅将连续特征也改为逐列单层 ReLU MLP 嵌入后升至 91.72，其余架构与超参不变。
- 批大小消融（第 8 页正文 + 附录 E，第 15 页文字 / 第 16 页图 7）：训练 batch size 在 32~256 之间变化时，SAINT-i 的 AUROC 方差很小，与不含行间注意力的 SAINT-s 相当。
- 数据损坏鲁棒性（第 8 页正文"How robust is SAINT to data corruptions?" + 附录 E，第 15 页文字 / 第 16–17 页图 6）：用 CutMix 替换 10%~90% 特征模拟噪声/缺失，70% 损坏比例之前 AUROC 下降很小；行间注意力变体（SAINT / SAINT-i）对噪声更稳健，纯自注意力变体（SAINT-s）对缺失更稳健。

## 行间注意力技术问答（面向本课题的专项核实）

1. **一行如何"看到"其他行？** 把该行全部特征嵌入拼接成一个 n·d 维向量，将 batch 内 b 行的这些向量当作长度 b 的序列，对该序列做标准缩放点积多头自注意力（式 2、算法 1，第 4–5 页）。查询/键/值都建立在"整行"这一粒度上，而不是逐特征跨行匹配。
2. **batch 内还是全局？** 明确是**当前训练 mini-batch 内**："the attention is computed across different data points (rows of a tabular data matrix) in a given batch rather than just the features of a single data point"（第 4 页，3.2 节）。没有跨 batch 的记忆库、检索索引或全局候选池。
3. **训练与推理时候选集合如何构成？** 训练阶段候选集合就是当前 shuffle 后的训练 mini-batch，随机组成，没有时间或因果约束；批大小消融证实 32~256 的批组成对结果影响很小（第 8 页；附录 E，第 15–16 页）。**推理阶段候选批具体如何构成，论文正文和附录均未显式说明**（既没有讨论固定验证/测试批大小的规则，也没有讨论单样本推理时如何触发该层），这是一处需要查官方代码才能核实的空白，本笔记标为"疑问/待验证"。
4. **复杂度与显存代价？** 按算法 1 伪代码推导（论文正文未给出显式复杂度表达式，此处为**推导而非原文直接陈述**）：行间注意力等价于对长度 b、每 token 维度 n·d 的序列做自注意力，注意力矩阵为 b×b，代价随 batch size 呈平方增长、随 n·d 线性增长。实测代价见表 1（第 6 页）：SAINT-i 参数量是 SAINT-s 的约 3.85 倍，但因为只需 L=1 层（而 SAINT-s 需要 L=6 层）且更适合并行，单卡 RTX 2080Ti 上反而快约 14 倍（123 秒 vs 1759 秒）。全部实验在单张 Nvidia GeForce RTX 2080Ti 上完成，累计约 4 GPU 天（第 14 页，附录 C）。
5. **是否是"把跨样本聚合信息注入表格模型"的先例？** 是。作者在引言明确称其为"novel intersample attention"（第 2 页），并给出两种直觉类比：一是"类似最近邻分类，但距离度量是端到端学习出来的而非固定的"（第 2 页，引言）；二是"完全图上的图注意力网络（GAT），所有表格行两两相连"（第 3 页）。相关工作节（第 2 页）对比了 Axial Transformer、MSA Transformer、TABBIE 等更早的行/列注意力工作，指出它们让"同一特征跨行通信"，而 SAINT 让"不同行的全部特征互相通信"（第 4 页，3.2 节："intersample attention allows all features from different samples to communicate with each other"）。此外，第 8–9 页（5.2 节，图 3–4）的注意力可视化显示，行间注意力在 MNIST 上高度稀疏——"very few points in a batch receive attention"（第 9 页），说明学到的是对少数"关键锚点"样本的软聚焦，而非对全体其他行的均匀平均。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系（本课题可迁移机制）

- SAINT 提供了"跨样本注意力可以提升表格分类"这一大方向的可行性证据（第 7 页，表 2：SAINT/SAINT-i 全面超过纯自注意力的 SAINT-s 与提升树基线），尤其是"特征多、样本少"场景增益更明显——"whenever there are few training data points coupled with many features...SAINT-i outperforms SAINT-s significantly"（第 8 页，"When to use intersample attention?"，Arcene/Arrhythmia 数据集为证）。这为本课题在特征列较多、单实体样本较稀疏的子集上尝试跨样本信息提供了动机层面的旁证。
- "当某行缺失或有噪声时，行间注意力可以从 batch 内相似样本借用对应特征"（第 4 页，3.2 节）这一动机与本课题想用"实体历史信息补全/增强当前行表征"的目标在直觉上同构，但补充信息的**来源完全不同**（详见下节"与 M-A 的差量"）。
- 连续特征逐列嵌入的消融（第 8 页，89.38→91.72）说明"给数值特征加独立嵌入层打破简单线性混合"本身就是一个独立于行间注意力的有效增益来源，FT-Transformer/TabM 等基座已经采用了类似做法，可以作为本课题现有基座已经吸收该经验的佐证，不需要再从 SAINT 重新引入。

## 与 M-A 的差量

M-A 拟把"实体因果前缀统计量"（该实体到当前流为止的历史聚合量）作为额外字段 token 输入 FT/TabM。逐条对照 SAINT 已做/未做：

- **已做**：证明了"让一行的表征吸收其他行信息"这一大类机制在表格任务上能带来实测增益（第 7 页，表 2），也证明了在特征缺失/噪声场景下，从"别的样本"借信息能提高鲁棒性（第 4 页，3.2 节；附录 E 图 6，第 15–17 页）。这是"跨样本聚合信息注入表格模型"的一个可引用先例。
- **未做，差异 1（聚合对象：跨实体 vs 同实体）**：SAINT 的行间注意力候选集合是当前 batch 内**任意其他样本**，不区分是否属于同一"实体"；论文全部 16 个数据集（第 6–7 页，表 4）本身就没有实体概念，每行即独立样本。M-A 要聚合的是**同一实体自身**的历史流量，二者在"聚合对象"维度完全不同：SAINT 做的是跨实体、跨行的软聚合（学习哪些"别的行"值得关注），M-A 做的是同实体内部的确定性统计聚合。
- **未做，差异 2（因果时序约束）**：训练用随机 65/15/25 划分和标准 shuffle mini-batch（第 7 页，"Training"），行间注意力候选没有任何时间先后的显式约束。论文全部 16 个数据集都是静态 i.i.d. 分类任务，没有时间戳字段，作者也没有讨论过如何给该机制加因果掩码。若不改造直接套用到跨年度检测场景，存在把同批次内"未来"样本信息注入"当前"行表征的结构性泄漏风险。M-A 的因果前缀统计量则被设计为严格只使用"该实体到当前流为止"的历史，天然满足因果单调性。
- **未做，差异 3（推理时对其他样本的依赖）**：行间注意力架构上要求训练和推理都提供"一个 batch 的其他行"参与计算（第 4 页，3.2 节），论文没有讨论单样本实时推理时该层如何退化（对应前一节"技术问答"第 3 点的空白）。M-A 是把统计量预先算好，作为一个固定的额外字段 token 拼进单行输入，推理时不依赖同批其他样本存在，可单条流独立完成预测。这是运行时依赖上的关键差异：SAINT 的跨样本通路是运行时的、依赖同批候选、无因果保证；M-A 的跨时刻通路是预计算的、单行自包含、因果有保证。

一句话结论：SAINT 证明了"给表格模型加一条跨行信息通路能带来增益"这个方向本身可行，但它的跨行聚合是**同批内、无因果约束、跨实体**的软聚合，与 M-A 要求的**同实体、因果、预计算为字段**的聚合在对象选择和时序保证上完全不同；只能把 SAINT 当作"跨样本信息有用"这一动机层面的旁证，不能把其架构或增益数字直接当作 M-A 有效性的证据。

## 不可直接声称的内容

- 全部 16 个数据集均为 UCI/AutoML 静态 i.i.d. 分类任务（第 6–7 页，表 4），无时间戳、无跨年度评价、无实体概念；不能把 SAINT 在这些基准上的 AUROC 增益直接当作"该机制在时序漂移/跨年度加密流量检测上同样有效"的证据。
- 训练用随机 65/15/25 划分（第 7 页），行间注意力候选集合无因果约束；不能声称该机制"天然适配因果时序场景"，反而若直接套用需要额外设计候选限制或因果掩码，论文未提供这类设计。
- 推理阶段候选批构成规则论文未明确说明，不能声称"SAINT 在单条流实时推理下无需其他样本陪同"。
- 论文没有做控制参数量的等容量消融来隔离"跨样本聚合"这一动机本身与"参数量增大"这一副作用（SAINT-i 参数量约为 SAINT-s 的 3.85 倍，第 6 页，表 1）；不能把 SAINT-i 相对 SAINT-s 的增益单纯归因于跨行信息，其中也混有容量增长的贡献。
- 表 2 的基线结果部分引自原论文（带 * 号标注，第 7 页表 2 脚注），部分为作者复现，两者精度可比性未经第三方独立复核；不能把 SAINT 相对 XGBoost 的领先幅度当作在本课题特征表上会重现的确定量级。

## 疑问 / 待验证

- 推理阶段行间注意力具体候选批如何构成（训练批固定、还是验证/测试阶段用不同批组成、是否允许跨越 train/val/test 边界）——原文未说明，需查官方代码或做本课题内的最小复现实验核实。
- 复杂度 O(b²·n·d) 是根据算法 1 伪代码推导得出，论文正文未给出显式复杂度表达式，引用时须标注为"推导"而非原文直接陈述。
- 行间注意力在大 batch（>256）或强时间相关性数据流上是否仍稳定：批大小消融只测到 256（附录 E，第 15–16 页），且全部是 i.i.d. 表格数据，缺乏时序场景下的证据，需另行验证。

## 可引用的逐字原文（≤15 词）

- "Intersample attention is akin to a nearest-neighbor classification"（第 2 页，引言）

## 证据记录

- 来源类型：完整论文（18 页，含正文 12 页 + 附录 A–F 6 页；带页码标记文本逐页核对，sha256 已记录）
- 支持：行间注意力机制的公式、伪代码、复杂度推导、跨样本借用信息的动机描述均逐页核实；主结果表 2、成本表 1、消融数字均标注页码
- 限制：全部数据集为静态 i.i.d. 表格分类任务，无时序/实体概念；推理阶段候选批构成未在原文说明；未做等容量消融
- 论断强度：有支持（行间注意力在 i.i.d. 表格分类上的增益及成本特征）/ 推论（迁移到本课题跨年度实体级检测场景）

## 文献信息

- arXiv：<https://arxiv.org/abs/2106.01342>
