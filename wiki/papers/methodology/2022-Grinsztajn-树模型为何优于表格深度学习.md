---
title: "Why do tree-based models still outperform deep learning on tabular data?"
authors: [Léo Grinsztajn, Edouard Oyallon, Gaël Varoquaux]
year: 2022
date: 2026-08-13
journal: "arXiv:2207.08815v1 [cs.LG]，2022 年 7 月 18 日，33 页，首页标注 Preprint. Under review（本 PDF 未标注 NeurIPS 2022 Datasets and Benchmarks 版式）"
source_pdf: "[[raw/papers/methodology/2022-Grinsztajn-Why-Tree-Based-Models-Outperform-Deep-Learning-Tabular.pdf]]"
sha256: "3baeb241e4f50981deb6e8e81f29192b1a84f1abde990d5fe8df4e594d993d6f"
tags:
  - 简单基线
  - 表格数据
  - 树模型
  - 归纳偏置
  - 评价方法论
  - 类型/论文
key_finding: "在 45 个数据集、每个学习器约 400 次随机搜索、总计 20,000 计算小时的统一预算下，树模型（XGBoost/GBT/RandomForest）在中等规模表格数据上对所有随机搜索预算都优于 MLP、Resnet、FT-Transformer 与 SAINT（摘要与第 6 页 4.2 节；图 1、图 2，第 5 页）。"
method: "先建立 45 个数据集的表格基准与统一超参搜索协议，再通过对数据施加变换（目标函数高斯核平滑、按特征重要性删特征、加入无信息高斯特征、随机旋转特征空间）反推两类模型归纳偏置的差异"
baseline: "RandomForest、GradientBoostingTrees/HistGradientBoosting、XGBoost 对比 MLP、Resnet、FT_Transformer、SAINT"
aliases:
  - Grinsztajn2022-树模型仍占优
  - Why do tree-based models still outperform deep learning
related:
  - "[[2022-ShwartzZiv-表格数据深度学习并非必需]]"
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
  - "[[2018-Shen-SWEM简单词嵌入池化基线]]"
---

# 树模型为何仍在表格数据上胜过深度学习

> Grinsztajn, Oyallon, Varoquaux，2022，arXiv:2207.08815v1 · 33 页

## 一句话

作者先用 45 个数据集和统一的随机搜索预算证明树集成在中等规模表格数据上全面胜过包括 Transformer 在内的深度模型，再用四类数据变换定位原因：目标函数不光滑、表格数据含大量无信息特征、以及 MLP 类模型的旋转不变性会丢掉"每列各有含义"这一关键先验。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Why do tree-based models still outperform deep learning on tabular data?
- arXiv：2207.08815v1 [cs.LG]，2022 年 7 月 18 日（第 1 页左侧竖排标记）
- DOI：未在原件中定位（本 PDF 版本标注 "Preprint. Under review"，第 1 页页脚）
- 原件：`raw/papers/methodology/2022-Grinsztajn-Why-Tree-Based-Models-Outperform-Deep-Learning-Tabular.pdf`
- 代码与原始搜索结果：<https://github.com/LeoGrin/tabular-benchmark>（第 4 页，3.3 节）

## 核心方法

- 数据集纳入判据（第 3 页，3.1 节）：列必须异质；`d/n < 1/10`；剔除时间序列与流式数据（要求 I.I.D.）；剔除人工数据；样本数 ≥ 3,000 且特征数 ≥ 4；剔除"太容易"的数据集（默认逻辑回归得分与默认 Resnet 及默认 HistGradientBoosting 的相对差距低于 5%）；剔除目标是数据确定性函数的数据集。
- 去除旁支问题（第 3 页，3.2 节）：训练集截断到 10,000 样本以研究中等规模区间；删除全部缺失数据；分类任务二值化并使两类样本各占一半；删除取值超过 20 类的类别特征；删除唯一值少于 10 的数值特征。
- 超参协议（第 4 页，3.3 节）：每个数据集每个模型跑约 400 次随机搜索，随机搜索总是从默认超参开始；对随机搜索顺序做 15 次重排以获得 bootstrap 式的"给定预算下期望测试分数"曲线。
- 聚合指标（第 4 页，3.4 节）：以分类准确率与回归 R² 为基准分，用类似 ADTM 的仿射归一化跨数据集聚合，下界取 10%（分类）或 50%（回归）测试误差分位数而非最差模型。
- 机制实验（第 6–8 页，第 5 节）：(1) 用高斯核平滑器按不同长度尺度平滑训练集目标；(2) 按随机森林特征重要性从低到高逐步删特征，并单独训练"被删掉那部分特征"的 GBT；(3) 加入与目标和其他特征都不相关的标准高斯噪声特征；(4) 对高斯化后的特征做随机旋转。

## 关键数字（含页码/表号）

- 基准规模（摘要与第 2 页）：45 个数据集；每个学习器约 400 次随机搜索迭代；总计 20,000 计算小时；中等规模定义为约 10K 样本。
- 分面样本量（图 1、图 2，第 5 页）：仅数值特征的中等规模基准含 15 个分类与 19 个回归数据集；含类别特征的基准含 7 个分类与 14 个回归数据集。
- 主结论（第 6 页 4.2 节，图 1、图 2）："Tree-based models are superior for every random search budget, and the performance gap stays wide even after a large number of random search iterations"；且该对比尚未计入深度模型每次搜索迭代更慢的成本。**注意：本文主结果以曲线图给出，正文未提供逐数据集的数值表格，故无法引用具体准确率数字。**
- 类别特征不是主因（第 6 页 4.2 节）：只用数值特征时差距变窄，但"most of this gap subsists when learning on numerical features only"。
- 发现 1，目标函数不光滑（第 6–7 页，5.2 节，图 3）：小长度尺度的目标平滑显著降低树模型准确率，却几乎不影响神经网络，说明真实表格目标函数不光滑而神经网络偏好低频函数。
- 发现 2，无信息特征普遍存在（第 7 页，5.3 节，图 4）：删除按重要性排序最低的一半特征几乎不影响 GBT 准确率；仅用被删掉的特征训练 GBT，在删除比例达 20% 以内时测试准确率非常低，到 50% 仍偏低，说明这些特征多为无信息而非冗余。
- 发现 2 续（第 7 页，图 5）：删除无信息特征会缩小 MLP/Resnet 与树模型及 FT-Transformer 的差距，加入无信息高斯特征会拉大差距。
- 发现 3，旋转不变性有害（第 7 页，5.4 节，图 6）：随机旋转数据集后只有 Resnet 性能不变，且模型排序发生反转——神经网络反超树模型、Resnet 反超 FT-Transformer。作者据 Ng (2004) 指出，任何旋转不变学习过程的最坏情况样本复杂度至少随无关特征数线性增长。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 本课题今晚的实测排序（逐流 XGBoost AP=0.2244 高于逐流 MLP AP=0.1590）与本文在 45 个数据集上的系统结论完全一致，可用作"这不是本课题的偶发现象，而是表格类数据上的已发表规律"的引用来源。
- 提供了可直接复用的诊断实验：本课题的逐流特征表本质上是异质表格数据，可照搬 5.3 节做法——按随机森林重要性删除一半特征后重训 XGBoost 与 MLP，观察二者差距是否收窄。若收窄，则说明 MLP 落后的主因是无信息特征而非模型容量，据此可决定是补特征选择还是换模型族。
- 解释了本课题中神经网络路线的一个可能失败机制：流量特征列（包大小统计、时长、方向比例）各自有独立物理含义，属于典型的"非旋转不变数据"，而 MLP 与不带特征嵌入的序列模型会把它们线性混合，丢失该先验。这为"给数值特征加分箱或嵌入层以打破旋转不变性"提供了机制依据，但在本课题上仍属待验证假设。
- 该基准的纳入判据明确剔除了流式数据与时间序列（第 3 页，3.1 节），因此其结论只覆盖 I.I.D. 表格设定；本课题的逐流 I.I.D. 基线可以引用，跨年度时序外推部分不能引用。

## 局限（不可直接声称的内容）

- 基准明确要求 I.I.D. 数据并剔除时间序列与流式数据，不包含任何分布漂移、时间外推或跨年度评价，因此不能支持本课题关于"跨年度零样本迁移"的任何结论。
- 分类任务被强制二值化并做了类别均衡（每类保留一半样本，第 3 页），与本课题极不平衡、以 AP 与 DR@4%FPR 为主指标的设定不同；本文使用准确率与 R²，其结论不能直接迁移到稀有正类指标。
- 训练集截断到 10,000 样本，作者自陈未回答很小与很大数据集上的情况（第 8 页，Limitation）。
- 全部缺失数据被删除，作者把缺失值处理列为未解决问题（第 8 页）。
- 论文没有实体级聚合与逐样本预测的对比，不能用于支持本课题"实体级聚合后 AP 提升到 0.5233–0.5475"这一结论。
- 主结果只有图未有数值表，任何引用只能引用趋势与排序，不能引用具体数值。

## 可引用的逐字原文（≤15 词）

- "Tree-based models are superior for every random search budget"（第 6 页，4.2 节）
- "neural networks struggle to learn irregular patterns of the target function"（第 2 页，引言）

## 证据记录

- 来源类型：完整论文（33 页，`pdftotext -layout` 抽取后逐页核对；`file` 判定为 PDF 1.5，sha256 已记录）
- 支持：统一预算下树模型在中等规模表格数据上稳定优于深度模型；无信息特征与旋转不变性是可实验验证的解释机制
- 限制：I.I.D. 设定、类别均衡、准确率指标、无漂移、无实体级聚合、主结果无数值表
- 论断强度：有支持（表格数据上树模型优势与其成因）/ 推论（迁移到加密流量跨年度检测）

## 文献信息

- arXiv：<https://arxiv.org/abs/2207.08815>
- 基准与原始随机搜索结果：<https://github.com/LeoGrin/tabular-benchmark>
