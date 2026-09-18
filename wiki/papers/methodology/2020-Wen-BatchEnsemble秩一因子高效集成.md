---
title: "BatchEnsemble: An Alternative Approach to Efficient Ensemble and Lifelong Learning"
authors: [Yeming Wen, Dustin Tran, Jimmy Ba]
year: 2020
date: 2026-08-28
journal: "ICLR 2020 会议论文（首页标注 Published as a conference paper at ICLR 2020），arXiv:2002.06715v2，20 页"
source_pdf: "[[raw/papers/methodology/2020-Wen-BatchEnsemble.pdf]]"
sha256: "9971405a14d7a23f7e12bbf748138536e1d1d941459a997109c12338be58256c"
arxiv_id: "2002.06715v2"
tags:
  - 集成学习
  - 秩一分解
  - 参数高效
  - 不确定性估计
  - 持续学习
  - 类型/论文
key_finding: "BatchEnsemble 用共享权重 W 与逐成员可训练秩一矩阵 Fi=ri·si^T 的哈达玛积生成每个成员的等效权重（第4页，式1），使集成在测试时提速3倍、显存降低3倍（集成规模4，摘要，第1页），CIFAR-100 上比单模型提升约2个百分点（78.32%→80.32%，第8页，表3）；但论文把成员间预测分歧做成的多样性指标（第10页第5节；附录E.1，第17页）只用作事后诊断解释，未作为任何下游决策规则的输入。"
method: "定义每层权重为共享慢权重 W 与逐成员秩一快权重 Fi=ri·si^T 的哈达玛积；通过输入乘 ri、共享权重矩阵乘法、输出乘 si 的向量化实现（式2–5，第4–5页），在单次前向中并行计算多个成员；训练时按成员切分 mini-batch 子批，测试时把输入复制 M 份一次前向得到全部成员输出后取平均"
baseline: "Vanilla 单模型、MC-dropout（Dropout 集成）、Naive Ensemble（独立训练的朴素集成）；持续学习场景对比 EWC、PNN、DEN、RCL"
aliases:
  - Wen2020-BatchEnsemble
  - BatchEnsemble秩一集成
related:
  - "[[2025-Gorishniy-TabM参数高效集成]]"
---

# BatchEnsemble：秩一因子实现的高效集成与持续学习

> Wen, Tran, Ba，2020，ICLR 2020 · arXiv:2002.06715v2 · 20 页

## 一句话

BatchEnsemble 把每个集成成员的权重表示为"所有成员共享的慢权重"与"每个成员独有的可训练秩一矩阵"的哈达玛积，使得多个集成成员可以在单次前向中并行计算，几乎不增加计算与显存开销；论文用一个独立的"预测分歧"指标解释了这种秩一扰动为何能带来足够多样性，但该指标全程只用于事后分析，从未被用作分类、校准或探索决策本身的输入。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：BatchEnsemble: An Alternative Approach to Efficient Ensemble and Lifelong Learning
- 会议：Published as a conference paper at ICLR 2020（第 1 页页眉）
- arXiv：2002.06715v2 [cs.LG]，2020 年 2 月 20 日（第 1 页左侧竖排标记）
- 原件：`raw/papers/methodology/2020-Wen-BatchEnsemble.pdf`
- 官方代码：<https://github.com/google/edward2>（第 1 页脚注 1）

## 论文原结论

### 秩一因子构造与前向公式

- 定义（第 4 页，3.1 节，式 1）：对某层权重 `W∈R^{m×n}`（输入维 m，输出维 n），第 i 个成员的等效权重 `W_i = W ∘ F_i`，其中 `F_i = r_i·s_i^T`，`r_i∈R^m`、`s_i∈R^n` 是该成员独有的可训练向量（"fast weights"），W 是全部成员共享的"slow weight"。
- 单样本前向（第 4 页，式 2–4）：`y_n = φ(W_i^T x_n) = φ(W^T(x_n∘r_i)∘s_i)`——输入先逐元素乘 `r_i`，过共享权重 W 做矩阵乘法，输出再逐元素乘 `s_i`，最后过激活函数 φ。
- 批量向量化形式（第 5 页，式 5）：`Y = φ(((X∘R)W)∘S)`，X 是 mini-batch 输入矩阵，R、S 的每一行分别是该样本所属成员对应的 `r_i`、`s_i`（把成员归属"广播"进 R、S 两个矩阵后即可用普通矩阵乘法一次算完整批）。

### 训练时成员如何分配到 mini-batch

- 第 5 页，3.1 节末尾（"To match the input and the ensemble weight..."）：把输入 mini-batch 划分成 M 个子批，每个子批固定分配给一个成员权重 `W_i`，即成员 i 在训练时只看到该 mini-batch 中属于自己的那一份数据。
- 第 5 页，3.2 节明确指出这是一个局限："if we keep the mini-batch size the same as single model training, each ensemble member gets only a portion of input data"，需要通过增大 batch size 弥补，"increasing the batch size incurs almost no computational overhead...on the hardware that can fully utilize large batch size"。
- 分类实验实例（第 15 页，附录 B "Classification"）：ensemble size=4、mini-batch=128 时每个成员实际只拿到 32 个样本（受限于 BatchNorm 至少需要 32 个样本才有效），训练轮数从单模型的 250 epoch 增到 375 epoch（多 50%）以弥补每成员数据量不足。
- 测试阶段则相反：把输入 mini-batch 复制 M 次得到有效批大小 B·M，令全部 M 个成员在一次前向中计算同一批 B 个输入的输出，再取预测平均（第 5 页，"Ensembling During Testing"）。

### 成员多样性来自哪里

- 主要来自快权重 `r_i, s_i` 的**随机符号向量初始化**（第 15 页，附录 B "Diversity Encouragement"）："we find it sufficient for BatchEnsemble to have desired diversity by initializing the fast weight (s_i and r_i in Eqn. 1) to be random sign vectors"，作者称之为"伪独立随机初始化"（pseudo-independent random initializations，第 10 页，第 5 节）。
- 次要来源是训练时每个成员看到不同的 mini-batch 子批（第 15 页，附录 B 同节："the scheme that each ensemble member is trained with different sub-batch of input can encourage diversity as well"）。
- 第 5 节给出直觉解释（第 10 页）：训练数据越少，参数收敛后越接近初始化，因此**初始化的多样性直接决定了集成的多样性**——"the diversity of initialization entirely determines the diversity of ensembling system"（第 10 页）。据此，Naive Ensemble（完全独立随机初始化）多样性最高，Dropout Ensemble（全部成员共享同一次初始化）多样性最低，BatchEnsemble（伪独立初始化）居中；附录 E.1 图 8（第 17–18 页）用实测的分歧-精度散点图印证了这一排序。

### 论文报告的多样性/不确定性指标

- **多样性度量**（附录 E.1，第 17 页）：定义为两个函数在测试集上"预测不一致的样本比例"（"the fraction of the test data points on which their predictions disagree"），取值 0（完全一致）~1（每个样本都不一致），并按错误率归一化以排除"随机预测反而多样性最高"的退化情况。第 10 页正文简述为"disagreement among ensemble members on test set"。
- **预测熵**（附录 C，第 16 页，图 7a）：对未知类别（分布外）样本计算平均后 softmax 的熵 `H(log p(y|x))`，用于比较单模型与集成方法在 OOD 样本上是否过度自信。
- **期望校准误差 ECE**（第 16 页，式 8）：`ECE=Σ_m (|B_m|/n)|acc(B_m)-conf(B_m)|`，用于衡量平均预测的置信度与准确率的差距（CIFAR-10：Single 3.27 / MC-drop 2.89 / BatchE 2.37 / NaiveE 2.32；CIFAR-100：9.28 / 8.99 / 8.89 / 6.82，第 16 页）。
- **上下文老虎机累计遗憾**（附录 D，第 17 页，表 4）：用 Thompson 采样评估不确定性质量，BatchEnsemble(size=8) 在均值排名上优于 Dropout 与部分基线。

### 论文有没有把成员之间的分歧当作可用信号

**原文没有把"多样性/分歧指标"本身直接作为下游任务的决策输入、置信度阈值或聚合权重使用。** 第 5 节和附录 E.1–E.2 的多样性度量只用于事后解释"为什么 BatchEnsemble 比 Dropout 集成效果好""为什么小数据集/过参数化网络上增益更大"（第 10 页开篇："beyond accuracy and uncertainty metrics, we are particularly interested in how much diversity rank-1 perturbation provides"），是一种**归因分析工具**，不进入模型的前向或决策路径。最终预测用的是各成员输出的简单平均（第 5 页，"we take the average of predictions of each ensemble member"），预测熵、ECE 等不确定性量也是基于这个平均后的分布计算，而非直接使用逐成员分歧的方差。唯一间接接近"用成员级随机性驱动决策"的地方是上下文老虎机实验："Thompson sampling samples from the policy given by one of the ensemble members"（第 17 页，附录 D）——这是**随机抽取单个成员的策略**去行动，用于探索/利用平衡，而不是"计算成员间分歧的一个数值并作为特征输入某个决策规则"。因此严格地说，原文未把成员分歧的量化值本身当作决策信号使用。

### 计算与显存代价关键数字

- 摘要（第 1 页）：集成规模为 4 时，测试时提速 3 倍、显存降低 3 倍。
- Split-CIFAR100 on LeNet（第 6 页，表 1）：相对 Vanilla 单模型，BatchEnsemble 计算成本 1.11×、显存成本 1.10×；对比 DEN 9.58×/5.31×、PNN 1.12×/4.16×、RCL 26.41×/2.52×。
- ResNet-32 集成规模 4（第 5 页，3.2 节）："BatchEnsemble of ResNet-32 of size 4 incurs 10% more parameters while naive ensemble incurs 3X more"。
- CIFAR 分类准确率（第 8 页，表 3）：CIFAR-10 Single 95.31% / MC-drop 95.72% / BatchE 95.94% / NaiveE 96.30%；CIFAR-100 Single 78.32% / MC-drop 78.89% / BatchE 80.32% / NaiveE 81.02%。

## BatchEnsemble 技术问答（面向本课题的专项核实）

1. **秩一因子怎么构造、前向公式是什么？** 见上"秩一因子构造与前向公式"，式 1（第 4 页）定义 `F_i=r_i s_i^T`，式 5（第 5 页）给出可并行的矩阵化前向 `Y=φ(((X∘R)W)∘S)`。
2. **训练时成员怎么分配数据？** 按 mini-batch 切子批，每个成员只看子批（第 5 页），需要增大总 batch size 或延长训练轮数弥补（第 15 页，附录 B）。
3. **多样性来自哪里？** 主要是快权重的随机符号初始化，其次是子批切分（第 15 页，附录 B）；第 10 页给出"初始化多样性决定集成多样性"的解释框架。
4. **论文有没有报告多样性/不确定性指标？** 有三类：预测分歧多样性度量（第 10 页正文，第 17 页附录 E.1 详细定义）、预测熵（第 16 页，OOD）、ECE（第 16 页，式 8）。
5. **论文有没有把成员分歧当决策信号用？** 没有——分歧指标只用于事后诊断/归因分析（第 10 页，附录 E），最终预测与不确定性评估都基于成员平均后的分布计算，原文未把成员分歧作为决策信号使用。

## 与 M-C 的差量

M-C 拟用 TabM 的 k=32 BatchEnsemble 式成员分歧（方差）作为不确定性信号进入实体级聚合或决策。逐条对照本文已做/未做：

- **已提供机制基础**：本文给出了"共享骨干 + 逐成员秩一缩放"这一高效集成的构造方式（第 4 页，式 1），并证实了成员多样性主要来自快权重的随机初始化与子批训练（第 10 页；第 15 页，附录 B）。这是 M-C 里"用 TabM(k=32) 生成多个隐式成员"这一步骤的直接理论来源；`2025-Gorishniy-TabM参数高效集成` 笔记已确认 TabM 把该机制应用到表格 MLP 并默认 k=32。
- **未验证，规模差异**：本文实验里的集成规模主要是 4（CIFAR/WMT/CIFAR corruption 均为 size=4），老虎机任务与 CIFAR-10 corruption 的 Dropout 对照测到过 size=8（第 17 页，表 4；第 6 页，图 5 说明），**论文完全没有测试或讨论 k=32 这种更大规模下秩一扰动的多样性是否仍然有效、是否边际递减**。把本文 size=4/8 的结论外推到 M-C 的 k=32，是一处需要用 TabM 自己的论文或本课题实验单独核实的空白，不能直接引用本文数字。
- **未做，核心差异（决策使用方式）**：本文从未把"成员分歧"这个量本身当作特征或不确定性分数送入任何后续决策（分类阈值、拒绝、路由、聚合权重等）；分歧度量只是论文用来解释方法有效性的事后分析工具（第 10 页；附录 E，第 17–18 页）。M-C 恰恰要做相反的事——把 k=32 个隐式成员在某条流上的预测方差当作一个**主动使用的不确定性特征**，输入到实体级聚合或决策规则里。这在原论文里没有先例、没有做过、也没有给出可行性证据，只能视为"待验证假设"，其可行性依据需要从 TabM 自身或本课题的消融实验里找。
- **任务域差异**：本文全部评价任务是 CV（CIFAR）、NLP（WMT）、上下文老虎机，没有表格数据实验，更没有实体级聚合或加密流量场景；是否在表格/实体级聚合场景下仍保持同样的多样性来源（随机符号初始化 + 子批训练）需要 TabM 或本课题独立验证，不能默认沿用。
- **训练协议细节需核实**：本文明确按子批切分数据给每个成员（第 5 页；第 15 页，附录 B），并指出"每成员实际数据量不足"是需要弥补的局限。若 M-C 依赖的 TabM 训练协议是让全部 k 个成员看到**相同**的每个 mini-batch（用不同 r_i, s_i 在同一批数据上并行跑出 k 个"虚拟模型"，多数 TabM 风格实现确实如此），那么多样性来源会更纯粹地依赖初始化随机性，而非"数据切分带来的额外多样性"——这会削弱本文"子批切分也贡献多样性"这条结论对 M-C 实际设置的适用性，需要用本课题/TabM 实际实现核实，不能默认沿用本文的训练协议细节。

一句话结论：BatchEnsemble 给出了 M-C 依赖的秩一高效集成构造与多样性来源解释，但原论文从未把成员分歧当作决策信号使用，且集成规模、任务域与训练协议都与 M-C 的实际设置（k=32、表格实体级聚合、TabM 训练方式）存在未验证的差距，只能作为机制来源引用，不能作为"分歧可用作不确定性信号"这一用法本身的证据。

## 不可直接声称的内容

- 本文全部实验为 CIFAR-10/100 图像分类、WMT14 机器翻译、Split-CIFAR/ImageNet 持续学习、上下文老虎机（第 6–10 页），没有表格数据或加密流量实验；不能把本文报告的准确率/效率增益直接当作"BatchEnsemble 机制在表格实体级检测任务上同等有效"的证据。
- 集成规模在全部主实验中最大为 4（CIFAR/WMT），仅在老虎机与部分校准对照测到 8（第 17 页，表 4）；不能把本文数字外推为"k=32 时秩一扰动依然提供足够多样性"的证据。
- 本文的多样性度量、预测熵与 ECE 全部基于事后分析或平均预测计算，从未作为决策规则的输入被验证有效；不能声称"成员分歧作为不确定性特征输入决策"这一用法已经被本文实验支持。
- 训练时按子批切分数据给各成员是本文的默认协议（第 5 页；第 15 页附录 B），若下游实现（如 TabM）采用不同协议（例如全部成员共享同一 mini-batch），本文关于多样性来源的解释不能不加验证地照搬。

## 疑问 / 待验证

- k=32 规模下秩一扰动的多样性是否仍然充分、是否存在收益递减——原文未测试，需依赖 TabM 论文或本课题自身消融实验验证。
- M-C 所依赖的 TabM 训练协议究竟是"子批切分"还是"全部成员共享同一 mini-batch"，会直接影响本文关于"数据切分贡献多样性"这条结论是否适用，需核实 TabM 官方实现。
- 成员分歧（方差）作为实体级聚合或决策的不确定性输入是否有效，原论文没有对应实验，需要在本课题内单独设计最小可证伪实验验证。

## 可引用的逐字原文（≤15 词）

- "the diversity of initialization entirely determines the diversity of ensembling system"（第 10 页，第 5 节）

## 证据记录

- 来源类型：完整论文（20 页，含正文 10 页 + 附录 A–G 10 页；带页码标记文本逐页核对，sha256 已记录）
- 支持：秩一权重生成公式、训练/测试时的批处理机制、多样性来源解释、成本对比数字均逐页核实；多样性/不确定性指标的定义与"未作为决策信号"这一判断均有明确页码依据
- 限制：无表格数据实验、集成规模未测到 32、成员分歧从未作为决策输入被验证
- 论断强度：有支持（秩一高效集成机制、其成本特征与多样性来源在原任务域上成立）/ 推论（迁移到本课题表格实体级、k=32、分歧作决策信号的用法）

## 文献信息

- arXiv：<https://arxiv.org/abs/2002.06715>
- 官方代码：<https://github.com/google/edward2>（第 1 页脚注 1）
