---
title: "TransTab: Learning Transferable Tabular Transformers Across Tables"
authors: [Zifeng Wang, Jimeng Sun]
year: 2022
date: 2026-09-02
journal: "NeurIPS 2022，arXiv:2205.09328，19 页（UIUC）"
source_pdf: "[[raw/papers/methodology/tabular-pretraining/2205.09328.pdf]]"
sha256: "0d0366590b2bc2670b7a64fb8b62c5f3e00a05afaf704f6139a5200dd60b548c"
tags:
  - 表格数据
  - 表格预训练
  - Transformer
  - 跨表迁移
  - 垂直分区对比学习
  - 对比学习
  - 类型/论文
key_finding: "TransTab 用列名文本化输入处理器接受变长列表格，配合垂直分区对比学习（VPCL）在 5 个临床试验数据集上的监督/增量学习/迁移学习场景分别排名 1.00/1.00/1.78（12 个方法中，摘要）；表6 显示监督 VPCL 在全部 5 个数据集上都优于监督基线，而普通监督迁移策略在其中 2 个数据集上反而低于不预训练基线（0.8183<0.8348、0.7239<0.7293）。"
method: "列名+单元格值拼成文本序列的输入处理器（分类/文本/数值/二值四类特征统一处理，§2.2）+ 门控 Transformer（§2.3）；预训练目标为垂直分区对比学习（VPCL，把样本的列垂直切成 K 个分区，分区间做对比学习，§2.4）"
baseline: "LR、XGBoost、MLP、SNN、TabNet、DCN、AutoInt、TabTransformer、FT-Transformer、VIME、SCARF（表2-表6）"
aliases:
  - TransTab
  - Wang2022-TransTab
  - VPCL
  - 垂直分区对比学习
related:
  - "[[2020-Huang-TabTransformer上下文嵌入与替换标记检测]]"
  - "[[2021-Somepalli-SAINT样本间注意力与对比预训练]]"
  - "[[2023-Zhu-XTab跨表预训练]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
---

# TransTab：垂直分区对比学习与跨表迁移

> Wang, Sun，2022，NeurIPS，arXiv:2205.09328 · 19 页

## 一句话

TransTab 把列名与单元格值一起文本化，使模型能接受任意变长列的表格（同一套参数可跨不同 schema 使用），并提出垂直分区对比学习（VPCL）——把一个样本的列切成若干分区、以分区为对比学习的正负样本单元；在 5 个临床试验数据集上，监督 VPCL 全面优于监督基线，而普通的「预训练后微调」迁移策略在其中两个数据集上反而拖累性能。

## 题录

- 题名（逐字抄自全文提取第 1 行）：TransTab: Learning Transferable Tabular Transformers Across Tables
- 作者与单位：Zifeng Wang、Jimeng Sun（UIUC）
- 会议：NeurIPS 2022；arXiv：2205.09328
- 原件：`raw/papers/methodology/tabular-pretraining/2205.09328.pdf`（19 页）
- 全文提取（阅读辅助，非原件）：`wiki/papers/methodology/tabular-pretraining/2022-Wang-TransTab-全文提取-mineru.md`
- **本笔记的定位单位是 arXiv 抽取全文的章节号、图号与表号，非印刷页码**——原件是预印本/会议版式的 mineru 转写，未保留原始排版页码。

## 论文原结论（章节号/表号）

- **四种应用场景（§2.1，图1）**：论文动机围绕四个此前表格模型无法处理的场景——S(1) 跨表迁移学习、S(2) 特征增量学习、S(3) 预训练+微调、S(4) 零样本推断，全部依赖「接受变长列表格」这一前提。
- **输入处理器（§2.2）**：类别/文本特征——列名与取值拼成文本序列，分词后查嵌入表得 `E_c∈R^{n_c×d}`；二值特征——仅当取值为 1 时才把该列名分词编码为 `E_b∈R^{n_b×d}`，取值为 0 时不进入后续计算（论文称此举显著降低高维稀疏 one-hot 特征的计算与内存开销）；数值特征——不与列名拼接（原文指出「分词-嵌入范式在区分数字上出了名地差」），而是先对列名单独编码得 `E_{u,col}`，再与数值相乘 `E_u = x_u × E_{u,col}`。三类嵌入过 LayerNorm 与同一线性层对齐后，与 `[cls]` 嵌入拼接为 `E = Ẽ_c ⊗ Ẽ_u ⊗ Ẽ_b ⊗ e^[cls]`。
- **门控 Transformer（§2.3，式1-3）**：`Z^l_att = MultiHeadAttn(Z^l)`（标准多头自注意力，式1式2）；门控层 `g^l = σ(Z^l_att · w^G)`（`σ` 为 sigmoid），`Z^{l+1} = Linear((g^l ⊙ Z^l_att) ⊕ Linear(Z^l_att))`（式3）——门控向量逐 token 控制该 token 嵌入进入下一层前的幅度。最终第 `L` 层的 `[cls]` 嵌入 `z^[cls]` 供分类器使用。
- **自监督 VPCL（§2.4，式4）**：样本 `x_i = {v_i^1,…,v_i^K}` 按列垂直切成 `K` 个分区（相邻分区可重叠，重叠比例按列数百分比确定）；同一样本的不同分区互为正对，其他样本的分区为负对；`K>2` 时**随机抽两个分区**计算，前向代价恒为 `2×` 而与 `K` 无关。
- **监督 VPCL（式5）**：正对放宽为「同类别的任意样本的任意分区」，负对为不同类别；论文论证普通监督预训练会使编码器偏向主要任务/主要类别、且超参跨数据集差异大，而 VPCL 借用监督对比学习的形式「对噪声与超参更鲁棒」。
- **监督学习结果（§3.1，表2）**：5 个临床试验数据集，TransTab 平均排名 `1.00(0.00)`（12 个方法中最优，逐数据集 AUROC 均为最高或并列最高，如 N00174655 上 `0.9428`）；FT-Transformer 是除 TransTab 外唯一显著超过 LR 的方法（表2 排名 `4.20`），LR 本身超过半数基线。
- **特征增量学习（§3.2，表3）**：TransTab 排名 `1.0(0.00)`，逐数据集 AUROC 全面领先第二名（如 N00041119 上 `0.6797` 对 LR 的 `0.6213`），证明其能利用跨阶段增量列而非丢弃旧数据或新特征。
- **跨表迁移学习（§3.3，表4）**：数据按列 50% 重叠切成 set1/set2，TransTab 在 set1 上预训练、set2 上微调（及互换），平均排名 `1.78(1.30)`（12 方法中最优）。
- **零样本学习（§3.4，表5）**：数据切成三等份 set1/set2/set3（列不重叠），模型只用 set1+set2 训练后直接推断 set3；ZSL 平均性能高于「只用 set3 训练」的监督基线（表5 逐列对比），作者归因于「ZSL 保留了 set1+set2 学到的知识」且「能利用比监督基线更多的数据量」；用 set1+set2 预训练再在 set3 微调的 transfer 设定综合两者优势，取得最佳性能。
- **VPCL 消融（§3.5，表6）——本论文对本课题最关键的一张表**：临床试验数据，Supervised（不预训训）`0.6313/0.8348/0.7444/0.6885/0.7293`；Transfer（普通监督迁移）`0.6424/0.8183/0.7458/0.6928/0.7239`；Self-VPCL `0.6412/0.8577/0.7486/0.7069/0.7348`；VPCL（监督）`0.6405/0.8583/0.7517/0.7063/0.7392`。作者原文（§3.5）：「普通迁移策略在两个数据集上损害了性能（`0.8183<0.8348`、`0.7239<0.7293`），而 VPCL 总是带来正效应」；分区数增加时 VPCL 相对 Self-VPCL 的优势扩大（图4）。
- **公开数据集上的负面对照（§3.5，表12）**：在**不相关**的公开表格数据上预训练时，「预训练对微调收益甚微，因为这些表定义了完全不同的列和目标任务」（原文方向），VPCL 与 Self-VPCL 相对监督基线的提升幅度明显小于表6（临床试验同域数据）的提升幅度。
- **总体摘要数字**：TransTab 在监督学习、特征增量学习、迁移学习三个场景分别排名 `1.00, 1.00, 1.78`（12 个方法中，摘要原文），预训练相对监督学习平均带来 `2.3%` AUC 提升。

## 可迁移机制（形式化，含超参具体值）

1. **垂直分区对比学习的目标函数**（式4式5）：自监督 `ℓ(X) = -Σ_i Σ_k Σ_{k'≠k} log[exp ψ(v_i^k,v_i^{k'}) / Σ_j Σ_{k'} exp ψ(v_i^k,v_j^{k'})]`；监督 `ℓ(X,y) = -Σ_i Σ_j Σ_k Σ_{k'} 1{y_j=y_i} log[exp ψ(v_i^k,v_j^{k'}) / Σ_{j'} Σ_{k'} 1{y_{j'}≠y_i} exp ψ(v_i^k,v_{j'}^{k'})]`，`ψ` 为余弦相似度，作用于分区 `[cls]` 嵌入的线性投影。`K>2` 时每步只随机采两个分区，前向代价恒为 `2×`。
2. **默认超参**（§3「Model and implementation protocols」）：2 层门控 Transformer，数值/词元嵌入维度 128，中间全连接隐藏维度 256，8 个注意力头，ReLU 激活，不启用 dropout；Adam，学习率 `{2e-5, 5e-5, 1e-4}`，无权重衰减，批量 `{16,64,128}`；自监督预训练最多 50 epoch，监督训练最多 100 epoch，早停耐心 10。
3. **垂直分区本身不依赖数值扰动分布**：VPCL 的正负对来自「列子集」而非「值扰动」，因此不需要像 TabTransformer 的 RTD 或 XTab 的破坏算子那样定义数值列的替换/扰动分布。
4. **门控层的逐 token 抑制机制**：`g^l = σ(Z^l_att · w^G) ∈ [0,1]^n` 逐 token 缩放注意力输出后再线性投影，是一个独立于 VPCL 的架构组件，可与列名文本化输入处理器分开评估。

## 不可直接声称的内容

- **列名文本化输入处理器依赖列名具备语言学语义**（§2.2「the column description decides the meaning of cells」），本课题字段是网络流统计量的固定数值列，**没有可供分词的自然语言列名语义**，该输入处理器的核心动机（跨表列名语义对齐）在本课题不适用。
- **表6的临床试验数据是五个小规模数据集**（表1，`748`–`3871` 样本），VPCL 相对监督基线的提升幅度最大处仅 `+0.0235`（N00174655，VPCL vs Supervised），最小处为 `-0.0008`（N00041119，VPCL vs Self-VPCL），**无种子方差报告，不能当作效应量引用**。
- **在不相关公开表格数据上预训练收益甚微**（§3.5，表12 原文方向），与可行性调研中「跨表权重不可迁移」的结论同向；不能把表6（同域临床试验）的正面结果当作「预训练在任意表格数据上都有效」的证据。
- **零样本推断依赖列重叠或至少部分共享语义**（图6，重叠比例影响 ZSL 性能），且论文自陈该方法的核心动机是列名可对齐的多表场景，与本课题单表单套字段口径的场景不匹配。
- 该论文没有做时间序列、因果前缀截断或实体级聚合的实验，评价指标为 AUROC，数据集为二分类，没有极端类别不平衡（本课题源年 20 个正实体）下的实验。

## 仍需实验验证的假设（本课题推论，明确标注）

- **推论 1**：VPCL 的目标可以脱离 TransTab 自身的「列名文本化」输入处理器单独移植——本课题骨干 FT-Transformer 的 FeatureTokenizer 已经逐字段独立参数化产出 Token（83 字段 + `[CLS]` = 84 Token），一个「垂直分区」即为一个 Token 子集，不需要依赖列名语义。**这是结构类比，未做任何实验**。
- **推论 2**：本课题 `11,991,315` 条流全部带标签，与监督 VPCL（式5，用标签构造正对）的适用前提直接契合，在族内两篇「无标注预训练全标注下收益不明显」自陈的背景下，监督 VPCL 恰好落在该证据缺口的另一侧。**该推论未经本课题任何实验验证**。
- **推论 3**：若本课题借鉴 VPCL，需要自行确定分区数 `K`、重叠比例，以及**按什么依据切分 83 个字段**（随机切分？按语义分组，如包统计量、时长统计量、方向比例各成一组？），论文未给出可直接采用的取值，须自行登记依据后再实验。
- **推论 4**：监督 VPCL 使用源年标签 `y23` 构造正负对，这不触碰最终测试隔离（`y23` 已被本课题逐流 BCE 损失使用），但需要为该机制单独登记「是否接触最终目标标签」的核验项，不能沿用 ETA 参数登记表中只覆盖 `α` 的口径。

## 与本课题的关系

本课题第三章骨干为从头训练的 FT-Transformer（83 字段：81 数值 + 2 词表，`n_layers=3`、`d_token=192`、`n_heads=8`、`ffn_hidden=255`，参数 `924,283`），训练流 `11,991,315` 条全部带标签。TransTab 对本课题的相关性集中在 VPCL 这一目标形式，而非其输入处理器：

1. **VPCL 是三篇候选中唯一不需要定义数值字段扰动/替换分布的预训练目标**——它靠列子集构造视图，天然绕过了 TabTransformer（阻断A：RTD 只定义类别列）与 XTab（需要经验边缘分布重采样）都必须解决的「数值列怎么加噪」问题。这是它相对本课题字段构成（81 数值 + 2 词表）的一个结构性优势。
2. **监督 VPCL 与本课题「全标注」的设定直接对应**，且用标签构造正对这一思路与本课题实体级检测的监督信号来源（`y23`）逻辑上相容，但具体是在逐流层面还是实体层面构造正对、如何与 ETA/BER 两个既有机制共存，本笔记不作推演，需专门设计。
3. **列名文本化输入处理器不适用于本课题**——本课题字段是固定语义的流统计量，不具备可供跨表对齐的自然语言列名，该部分的机制价值主要体现在多表迁移场景，与本课题单表单模型的边界不符。

## 我的理解

TransTab 论文标题强调的是「跨表可迁移」，但对本课题真正有用的部分反而是被作者称为「配套贡献」的 VPCL 目标本身——它是一种不依赖列名语义、也不依赖数值扰动分布定义的对比学习形式，可以脱离 TransTab 的输入处理器单独使用。论文自己也用表6和表12的对照说明了这一点的边界：VPCL 在同域数据上稳定有效，在不相关数据上收益甚微，这与「学到的是任务或域内的结构性对比信号，而非通用表格语义」这一判断相符，但这只是我的推论，论文没有做这层归因实验。

## 疑问 / 待验证

- 论文没有报告表6结果的方差或种子数（表2/表3/表4 明确写「10 个随机种子平均」，但表6未重复说明是否同样跑了多种子），本笔记按缺失处理，不代为假设已控制方差。
- 门控层（式3）与 VPCL 目标是两个独立组件，论文没有做「只用门控、不用 VPCL」或反之的消融，无法从本论文单独评估门控层的贡献大小。
- 监督 VPCL 在极端不平衡数据（如本课题源年 20 正实体对应的类别比例）下，正对采样是否会因少数类样本稀少而失效，论文的临床试验数据集正例比例最低为 `0.02`（NCT00174655，表1），量级上与本课题相近但未展开讨论采样策略在这种比例下的行为。

## 原始摘要

> Tabular data (or tables) are the most widely used data format in machine learning (ML). However, ML models often assume the table structure keeps fixed in training and testing. Before ML modeling, heavy data cleaning is required to merge disparate tables with different columns. This preprocessing often incurs significant data waste (e.g., removing unmatched columns and samples). How to learn ML models from multiple tables with partially overlapping columns? How to incrementally update ML models as more columns become available over time? Can we leverage model pretraining on multiple distinct tables? How to train an ML model which can predict on an unseen table? To answer all those questions, we propose to relax fixed table structures by introducing a Transferable Tabular Transformer (TransTab) for tables. The goal of TransTab is to convert each sample (a row in the table) to a generalizable embedding vector, and then apply stacked transformers for feature encoding. One methodology insight is combining column description and table cells as the raw input to a gated transformer model. The other insight is to introduce supervised and self-supervised pretraining to improve model performance. We compare TransTab with multiple baseline methods on diverse benchmark datasets and five oncology clinical trial datasets. Overall, TransTab ranks 1.00, 1.00, 1.78 out of 12 methods in supervised learning, feature incremental learning, and transfer learning scenarios, respectively; and the proposed pretraining leads to 2.3% AUC lift on average over the supervised learning.

## 文献信息

- arXiv：<https://arxiv.org/abs/2205.09328>
- 原件：`raw/papers/methodology/tabular-pretraining/2205.09328.pdf`
- 全文提取：`wiki/papers/methodology/tabular-pretraining/2022-Wang-TransTab-全文提取-mineru.md`
