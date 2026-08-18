---
title: "Tabular Data: Deep Learning is Not All You Need"
authors: [Ravid Shwartz-Ziv, Amitai Armon]
year: 2022
date: 2026-08-13
journal: "arXiv:2106.03253v2 [cs.LG]，版本日期 2021 年 11 月 23 日，正文标注 November 24, 2021，13 页（本 PDF 未标注 Information Fusion 期刊版式）"
source_pdf: "[[raw/papers/methodology/2022-ShwartzZiv-Tabular-Deep-Learning-Is-Not-All-You-Need.pdf]]"
sha256: "59db02f2323ba7289a43673c57fb2a77d588713b2043d719eb56e681d551a5c8"
tags:
  - 简单基线
  - 表格数据
  - 泛化到新数据集
  - 集成
  - 评价方法论
  - 类型/论文
key_finding: "四个宣称超越树集成的深度表格模型在其原论文之外的数据集上普遍退化：11 个数据集中 XGBoost 在 8 个上优于这些深度模型（p<0.005）；平均相对性能劣化 XGBoost 为 3.34%，而 NODE 14.21%、DNF-Net 11.96%、TabNet 10.51%、1D-CNN 7.56%（第 5–7 页，表 2、表 3）。"
method: "把 TabNet、NODE、DNF-Net、1D-CNN 与 XGBoost 放在 11 个数据集（含每篇原论文各 3 个与 2 个全新 Kaggle 数据集）上重跑，用 HyperOpt 贝叶斯搜索 1,000 步统一调参，用 Friedman 检验判定显著性，并额外构造深度模型与 XGBoost 的加权集成"
baseline: "XGBoost、SVM、CatBoost；集成变体：Simple Ensemble、Deep Ensemble w/o XGBoost、Deep Ensemble w XGBoost"
aliases:
  - Shwartz-Ziv2021-表格深度学习并非必需
  - Deep Learning is Not All You Need
related:
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
  - "[[2023-Zeng-Transformer对时序预测是否有效]]"
---

# 表格数据上深度学习并非必需

> Shwartz-Ziv, Armon（Intel IT AI Group），arXiv:2106.03253v2 · 13 页

## 一句话

四个各自宣称击败树集成的深度表格模型，一旦换到不是自己论文里的数据集就明显退化并输给 XGBoost；作者把这归因于选择偏差与调参投入不均，同时发现"深度模型 + XGBoost"的加权集成才是全局最优，而纯经典模型集成或纯深度集成都不行。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Tabular Data: Deep Learning is Not All You Need
- 作者单位：IT AI Group, Intel（第 1 页）
- arXiv：2106.03253v2 [cs.LG]，2021 年 11 月 23 日；正文首页日期 November 24, 2021
- DOI：未在原件中定位（本 PDF 无期刊版式与 DOI 标记）
- 原件：`raw/papers/methodology/2022-ShwartzZiv-Tabular-Deep-Learning-Is-Not-All-You-Need.pdf`

## 核心方法

- 被检验的四个深度模型（第 3 页，2.1 节）：TabNet（稀疏可学习掩码做软特征选择）、NODE（等深可微 oblivious 决策树集成）、DNF-Net（把析取范式软化为可微 DNNF 块的集成）、1D-CNN（先用全连接层造出带局部性的特征再叠 1D 卷积）。
- 集成构造（第 4 页，式 1、式 2）：式 1 为均匀权重混合 `p(y|x) = Σ_k p_{θ_m}(y|x, θ_m)`；式 2 用归一化验证损失 `l_k^val` 作权重加权，均匀权重是其特例。
- 数据集与划分（第 4–5 页，表 1）：11 个数据集，特征数 10 到 2,000，类别数 1 到 7，样本量 7,000 到 1,000,000；从 TabNet、DNF-Net、NODE 三篇论文各取 3 个，另加 2 个未被任一篇使用的 Kaggle 数据集；划分方式沿用原论文，随机划分时做 3 次重复，固定划分时用 4 个随机种子。
- 调参协议（第 4 页，3.1.2 节）：HyperOpt 贝叶斯优化，每个数据集跑 1,000 步；初始超参取自原论文；每个模型优化 6–9 个主要超参；训练至验证集连续 100 个 epoch 无改进为止。
- 关键术语（第 5 页）："unseen datasets" 指未出现在该模型原论文中的数据集，不是指未训练过的数据。
- 显著性检验（第 5 页）：Friedman 非参数检验，显著性水平 95%，p<0.05 拒绝原假设。

## 关键数字（含页码/表号）

- 泛化失败（第 5 页正文）："For 8 of the 11 datasets, XGBoost outperformed the deep models, which did not appear in the original paper"，且这些数据集上结果显著（p<0.005）。
- 平均相对劣化（表 3，第 7 页，数值越低越好）：Deep Ensemble w XGBoost 2.32%、Simple Ensemble 3.15%、XGBoost 3.34%、1D-CNN 7.56%、Deep Ensemble w/o XGBoost 6.91%、TabNet 10.51%、DNF-Net 11.96%、NODE 14.21%。（正文第 6 页把 XGBoost 记为 3.4%、DNF-Net 记为 11.8%，与表 3 存在小数位差异，引用时以表 3 为准。）
- 逐数据集结果（表 2，第 6 页，越低越好；YearPrediction 与 Rossman 为 MSE，其余为 ×100 的交叉熵）：Eye Movements 上 XGBoost=56.07±0.65，明显优于 NODE 68.35、DNF-Net 68.38、TabNet 67.13、1D-CNN 67.9；Gesture Phase 上 XGBoost=80.64±0.80 优于全部四个深度模型（最好者 DNF-Net 86.98）；Blastchar 上 XGBoost=20.39±0.21 优于 NODE 21.40、TabNet 23.72、DNF-Net 27.91。
- 深度模型只在自己论文的数据集上占优（表 2，第 6 页）：Gas 上 DNF-Net=1.44±0.09 优于 XGBoost 2.18；CoverType 与 Higgs 上 TabNet 分别为 3.01、21.14 优于 XGBoost 的 3.13、21.62；Epsilon 上 NODE=10.39 优于 XGBoost 11.12。
- 集成才是最优（表 2，第 6 页）：Deep Ensemble w XGBoost 在 CoverType（2.99）、Gesture（78.93）、YearPrediction（76.19）、MSLR（55.38）、Shrutime（13.10）、Blastchar（20.18）上取得最佳；11 个数据集中有 7 个上集成显著优于单个深度模型（p<0.005，第 6 页）。
- 缺一不可（第 7 页）：只用 XGBoost+SVM+CatBoost 的经典集成明显差于"深度模型 + XGBoost"集成，纯深度集成也不行，差异均 p<0.005。
- 子集选择（第 7 页与图 1，第 8 页）：按验证损失排序选模型时，只需三个模型即可接近最优集成性能；随机选择最差，前三个模型的差异显著（p<0.005）。
- 调参成本（第 7 页与图 2，第 9 页）：XGBoost 在超参搜索中收敛到好性能所需迭代次数少于深度模型；作者称在其实验中 XGBoost 比深度网络快"more than an order of magnitude"，但同时提醒运行时受实现优化程度影响，故改用"达到平台期所需迭代次数"作为与实现无关的代理指标。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 直接支持本课题"逐流 XGBoost（AP=0.2244）应作为主基线，且深度模型必须在同等调参预算下才允许比较"的做法。本文给出的失败机制——选择偏差与调参投入不均——正是本课题需要主动规避的评价陷阱。
- 该论文的"unseen datasets"设计与本课题的跨年度设定在动机上同构：都在检验"方法是否只在作者选定的数据上有效"。本课题的 LSPR23→LSPR24 零样本迁移可视为更严格的版本（同数据源、跨时间），可在论文中把本文作为"换数据集即退化"的先例引用，但要说明本文换的是数据集而非时间片，不是分布漂移的受控测量。
- 集成结论提供了一条可低成本验证的候选路线：本课题已有 XGBoost、MLP 与序列聚合三类模型，可按式 2 用归一化验证损失加权融合其打分，检验实体级 AP 是否超过单模型的 0.5233–0.5475。本文的证据表明"XGBoost 与深度模型互补、缺一不可"，但这一点在本课题上仍属待验证假设。
- 图 1 的"按验证损失选前三个模型即接近最优"给出了一个明确的成本控制经验，可用于限制本课题集成实验的规模。

## 局限（不可直接声称的内容）

- 实验全部为同分布的训练/验证/测试划分，没有时间外推或跨年度漂移，本文的"泛化到新数据集"不等于"分布漂移下的退化测量"。
- 指标为交叉熵与 RMSE，没有 AP、DR@FPR 等稀有正类指标，也没有报告类别不平衡处理，因此不能直接支持本课题的指标结论。
- 只有 11 个数据集，且 9 个来自被检验模型的原论文，覆盖面明显小于 Grinsztajn 等的 45 个数据集基准。
- 论文未评估实体级或分组聚合，与本课题"实体级聚合远优于逐流"的现象无直接证据关系。
- 作者自陈运行时对比受软件优化程度影响，速度结论只能定性引用（第 7 页）。
- 表 3 与正文第 6 页的数值存在小数位不一致，说明该 PDF 版本存在编辑遗留，引用时须以表 3 为准并注明。

## 可引用的逐字原文（≤15 词）

- "the deep models were weaker on datasets that did not appear in their original papers"（第 8 页，第 4 节）
- "we must take the reported deep models' performance with a grain of salt"（第 8 页，第 4 节）

## 证据记录

- 来源类型：完整论文（13 页，`pdftotext -layout` 抽取后逐页核对；`file` 判定为 PDF 1.5，sha256 已记录）
- 支持：深度表格模型换数据集即退化；XGBoost 是更稳健且更易调参的默认基线；深度模型与 XGBoost 的集成互补
- 限制：无分布漂移、无稀有正类指标、数据集数量有限、无实体级聚合证据
- 论断强度：有支持（表格数据上的基线选择与评价纪律）/ 推论（迁移到加密流量跨年度检测与集成路线）

## 文献信息

- arXiv：<https://arxiv.org/abs/2106.03253>
