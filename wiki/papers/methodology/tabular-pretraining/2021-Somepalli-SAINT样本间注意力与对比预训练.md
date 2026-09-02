---
title: "SAINT: Improved Neural Networks for Tabular Data via Row Attention and Contrastive Pre-Training"
authors: [Gowthami Somepalli, Avi Schwarzschild, Micah Goldblum, C. Bayan Bruss, Tom Goldstein]
year: 2021
date: 2026-09-02
journal: "arXiv:2106.01342，2021，18 页（University of Maryland / Capital One Center for Machine Learning；本地全文提取为预印本版式，未见正式会议出版信息）"
source_pdf: "[[raw/papers/methodology/tabular-pretraining/2106.01342.pdf]]"
sha256: "9069de09bcd867b6b8604460f5d98de678eef5a731fac0e2a4216fa850aad018"
tags:
  - 表格数据
  - 表格预训练
  - Transformer
  - 样本间注意力
  - 对比学习
  - 自监督预训练
  - 类型/论文
key_finding: "SAINT 变体在 14 个二分类数据集上平均 AUROC 达 93.13%（表2），全面超过 XGBoost（91.06%）、LightGBM（90.13%）、CatBoost（90.73%）等树模型；其消融（表9，14 数据集 50 标注点）显示仅对比预训练在完整 SAINT 上反而低于不预训练（85.58 对 85.78），只有「对比＋去噪」组合才带来净增益（86.96，+1.18）；同一篇论文也自陈全标注下预训练贡献不明显。"
method: "自注意力 Transformer 块（列间）与样本间注意力（intersample attention，MISA）块交替堆叠（式1、式2）；预训练阶段用 CutMix（原始空间）+ mixup（嵌入空间）生成增广视图，损失为 InfoNCE 对比项 + 逐字段重构去噪项（式5）"
baseline: "Logistic Regression、Random Forest、XGBoost、LightGBM、CatBoost（树模型/线性）；MLP、VIME、TabNet、TabTransformer（深度模型，表2、表3）"
aliases:
  - SAINT
  - Somepalli2021-SAINT
  - 样本间注意力
related:
  - "[[2020-Huang-TabTransformer上下文嵌入与替换标记检测]]"
  - "[[2023-Zhu-XTab跨表预训练]]"
  - "[[2022-Wang-TransTab垂直分区对比学习]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
---

# SAINT：样本间注意力与对比＋去噪预训练

> Somepalli, Schwarzschild, Goldblum, Bruss, Goldstein，2021，arXiv:2106.01342 · 18 页

## 一句话

SAINT 在标准的字段间自注意力之外，把整行特征拼成一个 token 后在样本之间做第二层注意力（intersample attention），并配合 CutMix+mixup 生成的对比+去噪预训练，在 14 个数据集上平均超过 XGBoost 等树模型；但消融显示纯对比学习单独使用反而拖累性能，必须与去噪组合才有效，且全标注场景下预训练本身收益有限。

## 题录

- 题名（逐字抄自全文提取第 1 行）：SAINT: Improved Neural Networks for Tabular Data via Row Attention and Contrastive Pre-Training
- 作者与单位：Gowthami Somepalli、Avi Schwarzschild、Micah Goldblum、Tom Goldstein（University of Maryland, College Park）；C. Bayan Bruss（Capital One Center for Machine Learning）
- arXiv：2106.01342，2021
- 原件：`raw/papers/methodology/tabular-pretraining/2106.01342.pdf`（18 页）
- 全文提取（阅读辅助，非原件）：`wiki/papers/methodology/tabular-pretraining/2021-Somepalli-SAINT-全文提取-mineru.md`
- **本笔记的定位单位是 arXiv 抽取全文的章节号与表号，非印刷页码**——原件是预印本版式的 mineru 转写，未保留原始排版页码。

## 论文原结论（章节号/表号）

- **整体架构（§3.1，图1(a)、式1式2）**：单层管线 `z_i^(1)=LN(MSA(E(x_i)))+E(x_i)`，`z_i^(2)=LN(FF_1(z_i^(1)))+z_i^(1)`，`z_i^(3)=LN(MISA({z_i^(2)}_{i=1}^b))+z_i^(2)`，`r_i=LN(FF_2(z_i^(3)))+z_i^(3)`——先字段间自注意力（MSA），再样本间注意力（MISA），二者堆叠 `L` 次。所有特征（类别与连续）都投影进同一 `d` 维空间再入 Transformer，并附加一个 `[CLS]` token（§3「Encoding the Data」），与 TabTransformer 只处理类别列不同。
- **样本间注意力实现（§3.2，算法1）**：把一个批次 `b×n×d` 的张量 reshape 成 `1×b×(n·d)`（每个样本的全部字段嵌入拼成一个向量），在这个「样本」轴上做标准自注意力，再 reshape 回去。多头情形下把 `q,k,v` 投影到 `d/h` 维再拼接。论文强调这与轴向/MSA Transformer/TABBIE 的行注意力不同：后者是「同一字段跨行通信」，MISA 允许「不同样本的全部字段互相通信」，可类比为在样本构成的完全图上做图注意力（§3.2 与 §2「Axial Attention」对照）。
- **代价与耗时（表1）**：SAINT-s（仅自注意力）`L=6, h=8`，`91.6M` 参数，`1759s`；SAINT-i（仅样本间注意力）`L=1, h=8`，`352.7M` 参数，`123s`；SAINT（两者都用）`L=1, h=8`，`347.3M` 参数，`144s`。**SAINT-i 参数是 SAINT-s 的 3.85 倍，耗时却只有约 1/14**（参数量与耗时按每 100 epoch 训练+推断，14 数据集均值，批量32测得）。
- **监督结果（§5.1，表2）**：14 个二分类数据集 + 2 个多分类数据集平均，SAINT `93.13%`、SAINT-i `93.09%`、SAINT-s `92.59%`，全部高于 XGBoost `91.06%`、LightGBM `90.13%`、CatBoost `90.73%`、Random Forest `89.52%`、MLP `84.59%`、TabTransformer `90.86%`。16 个数据集中 13 个由 SAINT 某变体夺魁（§5.1 原文）。
- **半监督结果（表3）**：50/200/500 标注点下，SAINT+预训练均领先绝大多数竞品；作者原文（§5.1「Semi-supervised setting」）：「有趣的是，当全部训练样本都有标注时，我们注意到预训练的贡献不明显，有无预训练的结果相当接近」——对照表3最后一列「All」，SAINT 无预训练 `93.13` 对 SAINT+预训练 `92.64`（预训练反而略低）。
- **连续特征嵌入的独立验证（§5.1「Effect of embedding continuous features」）**：把 TabTransformer 改造成对连续特征也做单层 ReLU MLP 嵌入（做法与 SAINT 一致）后，平均 AUROC 从 `89.38` 跳到 `91.72`，作者据此论证「嵌入连续数据很重要」——**这是本论文对 TabTransformer 架构限制的直接实证**。
- **样本间注意力的适用场景（§5.1「When to use intersample attention?」）**：字段数大、样本数少时 SAINT-i 显著优于 SAINT-s（举例 Arcene `200×783`、Arrhythmia `452×226`），且执行更快。
- **鲁棒性（§5.1「How robust is SAINT to data corruptions?」）**：CutMix 污染 10%–90% 特征时，AUROC 直到 70% 污染前下降都很小；SAINT／SAINT-i 相对 SAINT-s 更稳健（行注意力提升抗噪性）；但在大比例特征缺失场景下 SAINT-s／SAINT 更稳健，SAINT-i 反而不如，这是一条**方向相反的证据**，不能笼统说「样本间注意力总是更鲁棒」。
- **批大小敏感性（§5.1「Effect of batch size…」）**：批量 32–256 之间 SAINT-i 的性能变化「很小，与 SAINT-s 相当」。
- **注意力稀疏性（§5.2，图3b/3c）**：MNIST 上样本间注意力「极少的点获得注意力」，作者推测模型只聚焦少数难分类样本；该稀疏程度随数据集难度变化（Volkert 数据上更稠密）。
- **预训练消融（§E.1，表9，14 数据集 50 标注点平均 AUC）**：投影头研究——两个独立投影头最佳（SAINT: `86.96`）优于共享投影头（`86.89`）优于无投影头（`84.90`）；损失研究——**「无预训练」`85.78` 高于「仅对比」`85.58`**，「仅去噪」`86.21` 高于不预训练，「对比+去噪」`86.96` 最优；增广研究——**「无预训练」`85.78` 高于「仅CutMix」`85.37`**，「仅mixup」`86.45`，「CutMix+mixup」`86.96` 最优。**即单独的对比损失或单独的CutMix增广都不构成净增益，必须成对组合。**
- **默认超参（§5「Training」）**：AdamW，`β1=0.9, β2=0.999, weight_decay=0.01`，学习率 `1e-4`，批量 256（列多的数据集减小批量）；`p_cutmix=0.3, α(mixup)=0.2, λ_pt=10, τ(温度)=0.7`（全部数据集统一）。

## 可迁移机制（形式化，含超参具体值）

1. **样本间注意力的字面形式（算法1）**：`x: b×n×d → reshape(1,b,n·d) → self_attention → reshape(b,n,d)`。查询/键/值矩阵维度是 `(n·d)×(n·d)`（多头时 `(n·d)×(n·d)/h`），**参数量随字段数 `n` 与嵌入维 `d` 的乘积平方增长**，是该机制向大字段数、大嵌入维场景移植时的主要代价来源。
2. **CutMix+mixup 双重增广（§4，式3式4）**：`x_i' = x_i⊙m + x_a⊙(1-m)`（原始数据空间 CutMix，`m~Bernoulli(p_cutmix)`），`p_i' = α·E(x_i')+(1-α)·E(x_b')`（嵌入空间 mixup，`x_b'` 是另一随机样本 `x_b` 的 CutMix 版本）。**两次增广的配对伙伴各自独立随机选取**——先给每个样本随机选一个 CutMix 伙伴，嵌入后再随机选一个 mixup 伙伴。
3. **组合损失（式5）**：`L = -Σ log(exp(z_i·z_i'/τ)/Σ_k exp(z_i·z_k'/τ)) + λ_pt·Σ_i Σ_j L_j(MLP_j(r_i'), x_i)`，前项为 InfoNCE 对比损失，后项为逐字段重构损失（类别列交叉熵、连续列均方误差，`n` 个独立单隐层 MLP 头）。冻结超参 `λ_pt=10, τ=0.7`。
4. **投影头设计**：两个不同的单隐层 ReLU 投影头 `g_1(·), g_2(·)` 分别处理干净表征与增广表征，表9 证实「两个不同投影头」优于「共享投影头」优于「无投影头」。

## 不可直接声称的内容

- **仅对比学习不是增益来源**（表9研究2：`85.58 < 85.78`）——引用 SAINT 支持「加对比损失」时若不带这条限定，属选择性引用；同理仅 CutMix 增广也低于不预训练（`85.37 < 85.78`）。
- **表9 全部在 50 个标注点的半监督设定下测得**，不能当作全标注场景的效应量。
- **同篇论文自陈全标注下预训练贡献不明显**（§5.1「Semi-supervised setting」），与 TabTransformer 的自陈方向一致，但与 [[2023-Zhu-XTab跨表预训练]] 附录F、Rubachev 2022 的全标注实验方向相反——三方证据不一致，本文的自陈不能单独作为「预训练在全标注下无用」的定论。
- **鲁棒性结论方向不统一**：样本间注意力对噪声更稳健，但对大比例特征缺失反而不如纯自注意力（§5.1），不能笼统声称「MISA 总能提升鲁棒性」。
- **参数量代价未在论文中量化为相对骨干倍数**：论文只报告绝对参数量（表1，`347.3M`），未与本课题这类小骨干（百万参数级）对比；把 MISA 字面式移植到远小于 SAINT 骨干（91.6M–352.7M）的模型上时，注意力矩阵 `(n·d)×(n·d)` 的绝对代价相对骨干的比例会急剧放大，这一点论文未讨论。
- **16 个数据集样本量最大 495,141（Forest，表2表头），最小 200**，均为静态表格分类/回归任务，没有时间序列、因果前缀截断或实体级袋结构的实验。
- 表2/表3 的数据集含均衡与不均衡两类，但未专门报告不平衡场景下的分层结果，不能直接迁移到本课题实体极不平衡（源年 20 个正实体）的场景。

## 仍需实验验证的假设（本课题推论，明确标注）

- **推论 1**：样本间注意力若照搬到本课题的「实体袋」结构上（即在同一实体内的逐流之间做注意力，而非跨实体随机批次），可以规避 SAINT 原设计的已知弱点——一行的预测依赖恰好同批的其他行；因为实体袋是协议定义的固定单元而非随机批次。**这仅是结构类比，未做任何实验，是否有效未知**。
- **推论 2**：CLS-only 改编（只在逐流的池化向量上做样本间注意力，而非按算法1字面式把全部字段拼接）可将参数量控制在骨干量级以内，但**注意力矩阵的显存代价随袋大小平方增长**，在评价侧使用完整袋（而非训练截断袋）时是否可行，需要先核实评价协议下的最大袋大小分布，本笔记不重复该项已有的量化结果。
- **推论 3**：对比+去噪的组合预训练目标若要在本课题上实现，需要为 83 个数值字段逐一配置去噪重构头（类似论文的逐字段 `MLP_j`），且需要一个适合本课题字段分布的 CutMix/mixup 参数（`p_cutmix, α`），论文的 `0.3/0.2` 是否适用未经验证。
- **推论 4**：本课题预算远超论文的「light」微调场景（全部标签用于端到端训练很多轮），而论文本身在全标注下已自陈预训练收益不明显；能否在本课题预算下获得净收益，需要独立设计单臂先导实验而非直接采信本文的半监督结论。

## 与本课题的关系

本课题第三章骨干为从头训练的 FT-Transformer（83 字段、`d_token=192`、`n_heads=8`、`n_layers=3`，参数 `924,283`），检测在实体粒度（源年验证集 20 个正实体，袋大小中位数 2）。SAINT 提供两点直接相关的参照：

1. **样本间注意力与本课题「实体内逐流交互」诉求结构同型**：SAINT 的 MISA 是跨批次样本的行间注意力，本课题若要在实体袋内做逐流交互（而非仅用 ETA 的 top-k 聚合），MISA 是最直接的候选形式。但字面式的参数与显存代价（详见"不可直接声称的内容"）在本课题骨干规模下极不成比例，需先做代价核算。
2. **对比+去噪预训练目标与本课题「全标注」设定构成证据张力**：本课题 `11,991,315` 条训练流全部带标签，与 SAINT 自陈「全标注下预训练贡献不明显」的场景直接对应；这条证据应作为「是否值得为本课题引入独立预训练阶段」这一问题的谨慎信号之一，与 [[2020-Huang-TabTransformer上下文嵌入与替换标记检测]] 的同向自陈、[[2023-Zhu-XTab跨表预训练]] 的反向证据共同构成需要在本课题上单独验证的分歧点。

## 我的理解

SAINT 这篇论文最容易被误引的地方，恰恰是它自己用消融数据反驳了「加对比学习就有用」这个直觉——表9清清楚楚写着单用对比损失反而比不预训练差。真正起作用的是「对比+去噪」的组合，以及两种增广（CutMix+mixup）的组合。这提示一个更一般的教训：论文标题强调的机制（对比预训练）未必是论文自己实验里效果最大的部分，读消融表比读摘要更可靠。样本间注意力这个架构点本身相对独立于预训练目标，是两个可以分开评估的候选。

## 疑问 / 待验证

- 论文没有给出 MISA 相对骨干模型的参数倍数这一比例指标，只给了绝对参数量；对于远小于 SAINT 骨干规模的模型，这一比例可能极端不利，需要另行核算（不在本笔记重复计算结果，仅标注为待核实事项）。
- 表9的消融只在50标注点下测得，全标注下「投影头/损失/增广」三组消融的排序是否一致，论文未给出对应实验。
- 因果时序协议下（本课题的训练截断为因果前缀）袋内样本间注意力是否会引入未来信息泄漏，论文未讨论此类协议，需要本课题自行核验。

## 原始摘要

> Tabular data underpins numerous high-impact applications of machine learning from fraud detection to genomics and healthcare. Classical approaches to solving tabular problems, such as gradient boosting and random forests, are widely used by practitioners. However, recent deep learning methods have achieved a degree of performance competitive with popular techniques. We devise a hybrid deep learning approach to solving tabular data problems. Our method, SAINT, performs attention over both rows and columns, and it includes an enhanced embedding method. We also study a new contrastive self-supervised pre-training method for use when labels are scarce. SAINT consistently improves performance over previous deep learning methods, and it even outperforms gradient boosting methods, including XGBoost, CatBoost, and LightGBM, on average over a variety of benchmark tasks.

## 文献信息

- arXiv：<https://arxiv.org/abs/2106.01342>
- 原件：`raw/papers/methodology/tabular-pretraining/2106.01342.pdf`
- 全文提取：`wiki/papers/methodology/tabular-pretraining/2021-Somepalli-SAINT-全文提取-mineru.md`
