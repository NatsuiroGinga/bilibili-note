---
title: "XTab: Cross-table Pretraining for Tabular Transformers"
authors: [Bingzhao Zhu, Xingjian Shi, Nick Erickson, Mu Li, George Karypis, Mahsa Shoaran]
year: 2023
date: 2026-09-02
journal: "ICML 2023，arXiv:2305.06090，24 页"
source_pdf: "[[raw/papers/methodology/tabular-pretraining/2305.06090.pdf]]"
sha256: "dcc499005ec765512529998d8c73d5806d2b5ec29ba0031dcd0731c55d79f1e0"
tags:
  - 表格数据
  - 表格预训练
  - Transformer
  - 跨表迁移
  - 联邦学习
  - 破坏重构
  - 类型/论文
key_finding: "XTab 用「数据专属 featurizer/投影头 + 跨表共享 Transformer 骨干」的联邦预训练（FedAvg），在 AMLB 84 个下游任务上用重构目标 light 微调达 71.0% 胜率，heavy 微调降到 56.1%（图3）；附录F 消融进一步表明，全部增益中「在下游数据自身上做自监督预训练」贡献 64.8% 胜率，而额外的跨表外部知识只再多贡献 5.7 个百分点（附录F 表2）。"
method: "把 FT-Transformer/Fastformer/Saint-v 拆成数据专属 featurizer+投影头（不共享）与跨表共享 Transformer 骨干；用 FedAvg 联邦学习在多张表上联合预训练共享骨干；预训练目标含重构（破坏视图重建）、对比（InfoNCE）、监督三种（§3.1.3）"
baseline: "随机初始化的同架构 Transformer（baseline）；Random Forest、XGBoost、LightGBM、CatBoost、AutoGluon NN、FastAI、TransTab-cl（附录表14，原始预测性能对比）"
aliases:
  - XTab
  - Zhu2023-XTab
  - 跨表联邦预训练
related:
  - "[[2020-Huang-TabTransformer上下文嵌入与替换标记检测]]"
  - "[[2021-Somepalli-SAINT样本间注意力与对比预训练]]"
  - "[[2022-Wang-TransTab垂直分区对比学习]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
---

# XTab：跨表格 Transformer 预训练

> Zhu, Shi, Erickson, Li, Karypis, Shoaran，2023，ICML，arXiv:2305.06090 · 24 页

## 一句话

XTab 把表格 Transformer 拆成「数据专属的输入/输出层」与「跨表共享的中间骨干」，用联邦学习在 52 张预训练表上共同训练共享骨干；实验证明增益的大头（64.8% 胜率）来自「在下游表自身数据上做自监督」，跨表外部知识只贡献额外 5.7 个百分点，且该结果在完全监督微调（heavy）而非固定轮次微调（light）时明显衰减。

## 题录

- 题名（逐字抄自全文提取第 1 行）：XTab: Cross-table Pretraining for Tabular Transformers
- 作者与单位：Bingzhao Zhu¹²、Xingjian Shi³、Nick Erickson⁴、Mu Li³、George Karypis⁴、Mahsa Shoaran¹
- 会议：ICML 2023；arXiv：2305.06090
- 原件：`raw/papers/methodology/tabular-pretraining/2305.06090.pdf`（24 页）
- 全文提取（阅读辅助，非原件）：`wiki/papers/methodology/tabular-pretraining/2023-Zhu-XTab-全文提取-mineru_p1-20.md` 与 `_p21-24.md`
- **本笔记的定位单位是 arXiv 抽取全文的章节号、图号与表号，非印刷页码**——原件是预印本/会议版式的 mineru 转写，未保留原始排版页码。

## 论文原结论（章节号/表号）

- **模型结构（§3.1，图1）**：预训练阶段从不同表各采一个小批次（一批一表），featurizer 把每张表的列转成 token 嵌入（数据专属，不共享）；共享 Transformer 骨干处理变长 token 序列；输出经数据专属投影头做重构/对比/监督三种目标之一的损失。
- **Featurizer（§3.1.1）**：数值列 `k`：`W_k·x_k + b_k`（`W_k∈R^d` 可训练向量），类别列查嵌入表；文本单元当类别处理；附加一个 `[CLS]` token，特征嵌入 `E∈R^{c×d}`。
- **FedAvg 联邦预训练（§3.2，式1式2）**：每个客户端（一张表）本地梯度更新 `w_{k,i+1} ← w_{k,i} - α∇ℓ_k`；中央服务器聚合共享权重 `w_{i+N}^(S) ← w_i^(S) + Σ_k(w_{k,i+N}^(S) - w_i^(S))`，仅聚合共享部分；`N` 为每次聚合前的本地步数，论文默认 `N=5`（§3.2 与附录E消融）。
- **三种预训练目标（§3.1.3）**：重构——破坏视图 `x̃` 过骨干与投影头得 `x̂`，类别列交叉熵、数值列均方误差；对比——`(x,x̃)` 为正对，同批其他样本为负对，InfoNCE，投影头形式同 SimCLR；监督——投影头直接预测该表预定义标签列（论文称「target-aware pretraining」或「pre-finetuning」）。
- **破坏算子（§4.1「Table corruption」）**：随机选取每行一部分字段，从该列的**经验边缘分布**中重采样破坏，破坏比例**统一设为 60%**（援引 Bahri et al. 2021, SCARF 的建议），即每个样本 `x` 与破坏视图 `x̃` 之间 60% 条目被重采样、40% 保持不变。
- **默认模型配置（§4.2「Model configuration」）**：与 Gorishniy et al. 2021（FT-Transformer 原论文）相同——3 个 Transformer 块，特征嵌入维度 192，8 个注意力头，**前馈网络两层、尺寸与嵌入相同（即 `ffn_hidden=192`）**，注意力层 dropout 20%、前馈层 dropout 10%，激活为 ReGLU，Kaiming 初始化。批量 128，AdamW，学习率 `1e-4`，权重衰减 `1e-5`（不含 featurizer、`[CLS]`、LayerNorm、bias）。
- **数据与算力（§4.1、§4.2）**：AMLB 基准 104 个任务（71 分类 + 33 回归），52 个用于预训练、52 个用于下游微调（按任务名字母序划分）；下游数据 10% 测试、剩余 87.5%/12.5% 训练/验证，5 折重复；全部实验用 NVIDIA T4（16GB），约 **30,000 GPU 小时**。
- **微调设置（§4）**：light finetuning 固定 3 epoch；heavy finetuning 早停耐心 3、无 epoch 上限。
- **主结果（§4，图2）**：重构目标预训练，light 微调，随预训练步数（250/500/1000/1500/2000）增加，下游胜率、模型秩、归一化性能、误差下降率均单调改善。
- **不同预训练目标对比（§4，图3）**：**重构目标 light 微调胜率 71.0%，heavy 微调降到 56.1%**（均在 2000 预训练步）；作者原文归因于「深度模型的灾难性遗忘。由于表格 transformer 相对较小（FT-Transformer 骨干 `<1M` 参数），它们在微调阶段更易受灾难性遗忘影响」。三种目标排序：重构 > 对比 > 监督（§4 图3(c)(d) 秩比较）。
- **不同骨干对比（§4，图4）**：FT-Transformer、Fastformer、Saint-v 三种骨干在 XTab 预训练下均取得 >50% 胜率，跨表预训练的收益不依赖具体骨干实现。
- **可共享组件消融（附录B，图6）**：预训练全部 Transformer 块（不含 `[CLS]`）胜率与模型秩最优；**单独预训练 `[CLS]` token 不带来改进**，因为「`[CLS]` token 直接关系到下游预测，因而高度数据专属」；featurizer 与投影头因输入/输出维度逐表不同，天然不可共享。
- **预训练任务数量消融（附录D，图8）**：用 1 个任务、18 个任务、52 个任务预训练骨干，任务数越多下游胜率与模型秩越好。
- **联邦本地步数消融（附录E，图9）**：`N` 越大（每次聚合前本地更新步数越多）下游性能越差。
- **跨表知识与自预训练的分离（附录F，表2）**：三个臂——`w/o external task`（随机初始化→在下游训练集上预训练→微调）、`baseline`（随机初始化→直接微调）、`w/ external tasks`（XTab 跨表初始化→在下游数据上预训练→微调）。**全部以「无外部任务」（自预训练）为对照的胜率**：`baseline` 对自预训练胜率 `35.2%`（即完全不预训练输给自预训练 `64.8%`），`w/ external tasks` 对自预训练胜率 `55.7%`。**结论方向**：增益的大头来自「在自己数据上先做自监督」，跨表外部知识只多贡献约 5.7 个百分点。该表在 **heavy 设定、重构损失**下测得。
- **跨表迁移不兼容零样本**（附录C 原文方向）：「XTab 的优势并不随微调数据减少而更显著」，因 featurizer 与投影头仍需足够数据从头训练，「因此 XTab 不兼容零样本学习」。

## 可迁移机制（形式化，含超参具体值）

1. **经验边缘分布重采样破坏算子**（§4.1）：对类别列与数值列**一视同仁**，从该列自身的经验边缘分布重采样，无需定义噪声尺度或分布假设；破坏比例统一 `60%`（源自 SCARF 建议）。**这是三篇候选论文中唯一同时覆盖数值列与类别列、且不需要额外假设的破坏算子形式**，可与 TabTransformer 的 RTD（只定义类别列）互补。
2. **可共享组件规则**（附录B）：跨表预训练应覆盖全部 Transformer 块，**排除 `[CLS]` token**（数据专属，预训练它不带来改进）；featurizer 与投影头始终数据专属，微调阶段重新初始化。
3. **重构预训练目标形式**（§3.1.3）：类别列交叉熵、数值列均方误差的逐列重构，作用于破坏视图的骨干输出。
4. **模型配置基线**：`n_layers=3, d_token=192, n_heads=8, ffn_hidden=192`（与嵌入同维，非本课题合同的 `255`），dropout `attn=0.2, ffn=0.1`，ReGLU 激活，权重衰减 `1e-5`（排除 featurizer/`[CLS]`/LayerNorm/bias）。

## 不可直接声称的内容

- **图3的胜率是跨 84 个下游任务的比例，不是效应量**：`64.8%`（对照 baseline）或 `71.0%`（light 微调）这类胜率不等于任何具体指标的提升幅度，不能换算为「AUC 平均提升 X 个百分点」。
- **附录F 表2 的实验在 heavy 设定、重构损失下测得**，本课题预算远超 heavy（早停耐心3），处在图3那条随微调加重而衰减的曲线更右端，**该区间论文没有实验覆盖**。
- **附录C 明确「XTab 不兼容零样本学习」**——不能用来支持任何免微调、直接迁移权重的场景。
- **联邦学习（FedAvg）的目的是让多客户端分布式训练**，其价值在于让不同 schema 的表共用一套骨干并控制通信成本；本课题只有一张表、一套字段口径，联邦框架本身与本课题的适配场景无关，不应被当作「XTab 的核心创新对本课题适用」的证据。
- **实验用 NVIDIA T4（16GB）+ 84 个 AMLB 任务，规模远小于本课题**（训练流 `11,991,315` 条，单表），论文未测试过千万行级单表在该框架下的行为。
- 该论文的下游任务全部是**表格级预测**（分类/回归的单行预测），**没有实体级聚合、时间序列因果协议或极端类别不平衡（源年 20 正实体）**的实验设定。

## 仍需实验验证的假设（本课题推论，明确标注）

- **推论 1**：把破坏比例 `60%` 与经验边缘分布重采样直接套用到本课题 83 字段（81 数值+2词表）的重构预训练候选上是否合适，论文只在 AMLB 的一般表格任务上验证过，未在本课题字段分布上验证。
- **推论 2**：附录F「自预训练贡献 64.8% 胜率、外部跨表知识只再加 5.7 个百分点」这一结论方向，若成立，意味着本课题若要引入自监督预训练，**用自身 `11,991,315` 条流做重构预训练即可**，不需要额外获取跨领域表格数据——但这仍是待本课题独立先导实验验证的假设，不能直接采信论文在 AMLB 上的胜率数字。
- **推论 3**：本文与 [[2020-Huang-TabTransformer上下文嵌入与替换标记检测]]、[[2021-Somepalli-SAINT样本间注意力与对比预训练]] 两篇「全标注下预训练贡献不明显」的自陈方向相反（本文附录F 是全标注 AMLB 下游任务，仍测得 `64.8%` 胜率）。**这是文献内部的实质冲突，本笔记不代为调和**；可能的差异来源（均为推论，未验证）：族内两篇把预训练当半监督手段测（少标注+多无标注），本文把它当初始化与正则手段测（全标注）。该冲突需要额外的第三方证据（如 Rubachev 2022）裁决，不属于本篇论文自身能回答的问题。
- **推论 4**：本课题的模型合同 `ffn_hidden=255`，与本文默认配置 `ffn_hidden=192`（等于嵌入维）不同——若要借鉴本文任何与 FFN 宽度相关的量化结论（例如参数量或计算代价估算），需要按本课题实际配置重新核算，不能直接套用本文数字。

## 与本课题的关系

本课题第三章骨干为从头训练的 FT-Transformer（83 字段、`n_layers=3`、`d_token=192`、`n_heads=8`、`ffn_hidden=255`，参数 `924,283`），训练流 `11,991,315` 条全部带标签，只用 LSPR23 自身数据。XTab 提供三点直接参照：

1. **破坏算子的形式可直接借鉴**：经验边缘分布重采样同时覆盖数值列与类别列，解决了 TabTransformer RTD 只定义类别列的空缺，是本课题若实现自监督重构预训练时的候选破坏算子形式。
2. **附录F 的分解实验提示预训练收益的主要来源可能不依赖外部数据**：若本课题引入自监督预训练，论文的证据方向支持「先在自身数据上做重构预训练」这一最小可行路径，而非追求获取额外跨表数据（这也与本课题「只用 LSPR23 自有数据，不下载外部权重或跨表数据」的既定边界天然契合）。
3. **联邦学习框架与可共享组件划分不直接适用于单表场景**：本课题不存在多表 schema 差异的问题，FedAvg 与 featurizer/骨干拆分的动机（跨表 schema 不一致）在本课题不成立；但「预训练全部 Transformer 块、排除 `[CLS]`」这条设计规则不依赖多表场景，仍可作为设计参照。

## 我的理解

XTab 论文的标题聚焦「跨表」，但它自己在附录F给出的分解实验，反而揭示了一个可能更朴素也更重要的结论：大部分增益来自「先在下游表自身数据上自监督预训练」，跨表这件事本身贡献有限（约 5.7 个百分点的胜率差）。这对本课题很关键——本课题没有可用的跨表数据、也不打算获取，如果这个分解结论成立，说明「借鉴 XTab 的破坏算子形式，在本课题自身数据上做重构预训练」是一条无需 XTab 核心创新（跨表联邦）也能吸收其主要收益的路径。但这仍然只是一个待验证的推论，而且它与另外两篇论文（TabTransformer、SAINT）的全标注自陈方向相反，需要额外证据裁决。

## 疑问 / 待验证

- 附录F 的表述「w/ external task 有 55.7% 的胜率超过 w/ external task」存在明显的文字重复（原文如此，应为「超过 w/o external task」），本笔记按其定义表（三个臂的定义段落）与表2的行标「against w/o external task」还原正确读法，已在上文订正。
- 破坏比例 `60%` 援引自 SCARF（Bahri et al. 2021），本笔记未独立核验 SCARF 原文中该数值的推导依据，只记录 XTab 对它的援引与采纳。
- 本课题若采纳该破坏算子，替换分布应基于哪个统计窗口（全训练集？当前批次？）计算，论文未明确讨论在线/离线边缘分布估计的实现细节。

## 原始摘要

> The success of self-supervised learning in computer vision and natural language processing has motivated pretraining methods on tabular data. However, most existing tabular self-supervised learning models fail to leverage information across multiple data tables and cannot generalize to new tables. In this work, we introduce XTab, a framework for cross-table pretraining of tabular transformers on datasets from various domains. We address the challenge of inconsistent column types and quantities among tables by utilizing independent featurizers and using federated learning to pretrain the shared component. Tested on 84 tabular prediction tasks from the OpenML-AutoML Benchmark (AMLB), we show that (1) XTab consistently boosts the generalizability, learning speed, and performance of multiple tabular transformers, (2) by pretraining FT-Transformer via XTab, we achieve superior performance than other state-of-the-art tabular deep learning models on various tasks such as regression, binary, and multiclass classification.

## 文献信息

- arXiv：<https://arxiv.org/abs/2305.06090>
- 原件：`raw/papers/methodology/tabular-pretraining/2305.06090.pdf`
- 全文提取：`wiki/papers/methodology/tabular-pretraining/2023-Zhu-XTab-全文提取-mineru_p1-20.md`、`_p21-24.md`
