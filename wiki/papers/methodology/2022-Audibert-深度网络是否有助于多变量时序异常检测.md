---
title: "Do Deep Neural Networks Contribute to Multivariate Time Series Anomaly Detection?"
authors: [Julien Audibert, Pietro Michiardi, Frédéric Guyard, Sébastien Marti, Maria A. Zuluaga]
year: 2022
date: 2026-08-13
journal: "arXiv 预印本 2204.01637v1（首页标注 Preprint submitted to XXXXX, April 5, 2022）；正式版发表于 Pattern Recognition"
source_pdf: "[[raw/papers/methodology/2022-Audibert-Do-DNNs-Contribute-Multivariate-Time-Series-Anomaly-Detection.pdf]]"
sha256: "a5897a5d3b907f4e14babebea59ee06764bc8a4344f4ae8836ee13fb0ef560c6"
tags:
  - 负面结果
  - 多变量时序异常检测
  - 传统方法对照
  - 小样本训练
  - 类型/论文
key_finding: "16 种方法在 5 个数据集上的 Kruskal–Wallis 检验显示，F1 只有 SMD、AP 只有 SWaT 与 WADI 拒绝“三类方法中位数相同”的原假设，即多数情况下深度方法与传统方法无显著差异（第 13 页，5.2 节）。"
method: "把方法分为 conventional / machine learning / DNN 三类共 16 种，在 5 个公开数据集上用 F1（遍历 1000 个阈值取最优）与 AP 评价，并做 Kruskal–Wallis 与 Dunn 事后检验、训练集规模消融"
baseline: "MCUSUM、MEWMA、VAR、PCA、SSA、ICA、Matrix Profile；IF、LOF、DBSCAN、OC-SVM；AE、USAD、LSTM-VAE、DAGMM、OmniAnomaly"
aliases:
  - Audibert2022-DNN是否有贡献
  - Do DNNs Contribute to MTS Anomaly Detection
related:
  - "[[2021-Wu-Keogh-时序异常检测基准缺陷]]"
  - "[[2022-Kim-时序异常检测的严谨评价]]"
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
---

# 深度网络对多变量时序异常检测是否有贡献

> Audibert, Michiardi, Guyard, Marti, Zuluaga, 2022, arXiv 预印本 · 21 页

## 一句话

把传统统计方法、经典机器学习方法与深度方法放在同一基准里比较后，没有任何一类方法整体胜出；深度方法只在含上下文异常的 WADI 上显著更好，而当训练集缩小到 50% 以下时传统方法反超。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Do Deep Neural Networks Contribute to Multivariate Time Series Anomaly Detection?
- 单位：Orange、EURECOM、Orange Labs（第 1 页）
- arXiv：2204.01637v1 [cs.LG]，2022 年 4 月 4 日（第 1 页左侧竖排标记）；DOI 未在原件中定位
- 原件：`raw/papers/methodology/2022-Audibert-Do-DNNs-Contribute-Multivariate-Time-Series-Anomaly-Detection.pdf`

## 核心方法

- 三分类法（4.1 节，第 6 页）：conventional 假设数据由随机模型生成并估计模型参数；machine learning 不显式假设模型形式；DNN 是非线性机器学习的子类。
- 评价指标（5.1 节，第 12 页）：同时报告 F1 与 average precision（AP）。作者明确指出 AP 对正类（异常）敏感，因而适合高度不平衡的异常检测；F1 由归一化异常分数上遍历 1000 个阈值（步长 0.001）取最高值得到（第 13 页）。
- 统计检验（5.2 节，第 13 页）：对每个数据集用 Kruskal–Wallis 检验三类方法的中位数是否相同，显著时再用 Dunn 检验做两两事后分析。
- 训练规模消融（5.4 节，第 14–15 页）：在 SWaT 与 WADI 上保留最靠近测试集的 10%、25%、50%、75% 训练点分别重训。

## 关键数字（含页码/表号）

- 数据集（表 1，第 12 页）：SWaT 训练 496,800 / 测试 449,919 / 51 维 / 异常 11.98%；WADI 1,209,601 / 172,801 / 123 维 / 5.99%；SMD 708,405 / 708,420 / 28×38 / 4.16%；SMAP 135,183 / 427,617 / 55×25 / 13.13%；MSL 58,317 / 73,729 / 27×55 / 10.72%。
- F1 检验（第 13 页）：原假设仅在 SMD 上被拒绝（p<0.05），即 5 个数据集中有 4 个三类方法无显著差异。
- AP 检验（第 13 页）：原假设在 SWaT 与 WADI 上被拒绝；Dunn 事后检验显示 WADI 上 DNN 与 conventional 有显著差异（p<0.05），SWaT 上只有弱证据（0.1<p<0.05，按原文写法）；其余所有两两比较均无显著差异。
- 各族最优方法（表 2，第 14 页）：DNN 侧最优多为 USAD 或 OmniAnomaly，最差多为 DAGMM；conventional 侧 PCA、ICA、MCUSUM、SSA 分别在不同数据集上最优；VAR、SSA、MP 在 SWaT/WADI 上标注为“运行 10 天仍未收敛”。
- WADI 误检分析（5.3 节，第 14 页）：WADI 测试集共 14 处异常；4 处没有被任何 DNN 检出，7 处没有被 conventional 与 ML 方法检出；作者把 DNN 与传统方法的性能差距归因于若干上下文异常（如 1_MV_001 在 1_LT_001 达到阈值 40 之前开启，图 4，第 15 页）。注：正文该段先说“seven anomalies”未被传统方法检出，随后写“these three anomalies explain the performance gap”，原文数字表述不一致，此处照录。
- 训练规模（5.4 节，第 15 页）：训练集不超过 50% 时传统方法整体更好；SWaT 上 MP、PCA、ICA 在 50% 及以下的 AP 超过全部 ML 与 DNN 方法，OC-SVM 在 50% 时追平，只有保留 75% 训练数据时才被超越。传统方法的性能几乎不随训练集大小变化，ML 与 DNN 随数据增多而变好。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 支持“简单方法与深度方法差距通常不显著”的引用需求：本课题逐流 XGBoost AP=0.2244 高于逐流 MLP 0.1590 与完整 RWKV-7 状态递归，属于该论文统计结论覆盖的典型情形。可引用其 Kruskal–Wallis 结果说明“无显著差异”本身是可发表的结论。
- 支持本课题以 AP 为主指标：论文在第 12 页明确论证 AP 对正类敏感、适用于高度不平衡场景，与本课题异常/恶意占比极低的设置一致。
- 支持“数据规模决定方法族选择”的论证：训练数据不足时传统方法更稳（第 15 页），可用于解释本课题跨年度只有有限目标年数据时树模型更稳健。
- 一条需要谨慎的边界：论文的 F1 由测试集上遍历 1000 个阈值取最大值（第 13 页），这属于用测试集选阈值的乐观协议，本课题不应照搬该做法，只应引用其 AP 相关结论与统计检验框架。

## 局限（不可直接声称的内容）

- 五个数据集均为工控/服务器/航天遥测传感器序列，不含加密流量、不含跨年度分布漂移，也没有实体级（IP 对）聚合实验。
- 论文自陈（第 16–17 页）未系统分析计算开销，且 DNN 在 WADI 上的优势只在一个数据集观察到，需要更多含上下文异常的数据集验证。
- 所用 SMD、SMAP、MSL 数据集被作者自己引用 Wu & Keogh 标注为“可能存在缺陷”（第 12 页脚注段），因此其绝对分数不可直接作为方法能力的证据。
- 论文不提供“表示层失败但决策层聚合成功”的案例，不能用来支持本课题实体级聚合的具体机制。

## 可引用的逐字原文（≤15 词）

- “we show that no family of methods outperforms the others”（第 1 页摘要）
- “if the training set is not large enough, the conventional methods outperform the other two categories”（第 17 页结论）

## 证据记录

- 来源类型：完整论文（21 页全文，`pdftotext -layout` 抽取并逐页核对）
- 支持：三类方法在多数基准上无统计显著差异；小训练集下传统方法更优；AP 适用于不平衡异常检测
- 限制：无加密流量、无跨年度漂移、F1 使用测试集最优阈值
- 论断强度：有支持（方法族比较）/ 推论（迁移到加密流量跨年度任务）

## 文献信息

- arXiv：<https://arxiv.org/abs/2204.01637>
- DOI：未在原件中定位
