---
title: "Malware Detection by Analysing Network Traffic with Neural Networks"
authors: [Paul Prasse, Lukáš Machlica, Tomáš Pevný, Jiří Havelka, Tobias Scheffer]
year: 2017
date: 2026-08-13
journal: "IEEE Security and Privacy Workshops (SPW) 2017"
source_pdf: "[[raw/papers/methodology/multiple-instance/2017-Prasse-Malware-Detection-Network-Traffic-Neural-Networks-SPW.pdf]]"
sha256: "0ebc94847636a332cbbcbd32cb000d8baa4cf932801a0bc6a571e8a686d37362"
tags:
  - 加密流量检测
  - LSTM
  - 弱标注
  - 类型/论文
key_finding: "同一课题组 LSTM+域名神经嵌入方法的工作坊先行版本（数据规模约为 ECML 扩展版的六分之一），核心序列构造、聚合粒度与评价指标与 ECML 版一致，额外报告了'训练后首次出现的哈希'（真正未知恶意软件）子集的检测结果：R@70%P=26%、R@80%P=17%（第 209–210 页）。"
method: "与 [[2017-Prasse-加密流量LSTM恶意软件检测-ECML]] 相同：客户端×24小时为实例，10 条流为子序列（bag），LSTM（32单元+128 ReLU+softmax，50% dropout）处理流特征+域名神经嵌入，日级得分取子序列最大激活。"
baseline: "随机森林（相同特征堆叠）"
aliases:
  - Prasse2017-SPW
  - Prasse2017-网络流量LSTM
related:
  - "[[2017-Prasse-加密流量LSTM恶意软件检测-ECML]]"
---

# Malware Detection by Analysing Network Traffic with Neural Networks

> Prasse, Machlica, Pevný, Havelka, Scheffer, 2017 IEEE Symposium on Security and Privacy Workshops (SPW)，第 205–210 页，DOI 10.1109/SPW.2017.8。

## 一句话

这是 [[2017-Prasse-加密流量LSTM恶意软件检测-ECML]] 的工作坊先行版本，方法与序列构造完全一致，数据规模明显更小（约为 ECML 版的六分之一流量），额外单独报告了"训练后才首次出现的哈希"（即真正意义上未知的新恶意软件）子集上的检测表现。

## 序列构造与聚合层级

- 与 ECML 版本相同：分类实例＝客户端 × 24 小时（Section 5，"Client Malware Detection Problem"）；标签＝实例内是否存在至少一条恶意流；序列切分＝固定 10 条流一组的子序列（Section 6.3），LSTM 32 单元处理，128 ReLU+softmax 输出，50% dropout；日级得分＝全部子序列最大激活值。
- 标签来源同样基于 VPN 客户端记录可执行文件哈希 + VirusTotal 60 引擎投票（≥3 个判恶意标正，第 206 页），但 SPW 版本的标注规则略简化：不确定和未知哈希都统一标为"unknown”（第 206 页），未像 ECML 版那样把"未知哈希默认标良性”单列处理——即两篇论文的标签细则并非完全等价，属于扩展版对标注流程的进一步细化。

## 正类比例与评价指标

- **数据规模（明显小于 ECML 版）**：current data（2016年7月，5天，171个网络）共 **7,206,610** 条流、43,272 个不同客户端，23,093 个不同哈希，234,756 条恶意流 / 6,971,854 条良性流，恶意流占比约 **3.26%**（Table 1 前段落，第 206 页）；future data（2016年9月，8天，169个网络）10,159,990 条流、38,296 个客户端，30,004 个不同哈希，703,360 条恶意 / 10,159,990 条良性，占比约 **6.5%**。这两个比例都明显高于 ECML 扩展版的 0.81%/0.64%，说明扩展版补充的数据把正类稀释得更严重，评价难度更高。
- **评价指标**：与 ECML 版一致——Recall、Precision、R@x%P、PR 曲线、ROC 曲线（第 207 页 Section 5 "Client Malware Detection Problem"）。
- **关键数字**（Section 7.2，第 209–210 页）：
  - 10 折交叉验证（current data）：LSTM 在 70% 精度下召回 64%，90% 精度下召回 41%。
  - 跨时间评价（训练于 current、测试于 future）：70% 精度下召回 50%，90% 精度下召回 32%（性能相对 10 折 CV 有所下降，论文归因于"类别比随时间/公司变化”与"决策函数本身有轻微退化”两者叠加）。
  - **未知恶意软件子集**（首次出现哈希，训练数据中不存在）：70% 精度下召回 **26%**，80% 精度下召回 **17%**（第 209–210 页）——这是比"跨时间全量评价”更严格的泛化测试，专门排除了"训练时已见过的恶意软件哈希在未来重复出现”这种简单情形。
  - 平均检测时延：2.36 小时（全体），其中 52% 的检测发生在恶意应用发出第一条流后立即触发（第 210 页）。用户日均活跃约 8 小时。
  - Table 2（域名特征对比，与 ECML 版 Table 3 数字完全一致）：神经域名嵌入 R@70%P=0.84、R@80%P=0.79、R@90%P=0.73。

## 我的理解 / 与本课题的关系

SPW 版本相比 ECML 扩展版最有参考价值的地方是**未知哈希子集**的专门评价（26%@70%P、17%@80%P）——它比"跨时间全量评价”更贴近"模型是否真的学到了可泛化的行为模式，而不是记住了具体恶意软件的指纹”这一问题，这与本课题 LSPR23→LSPR24 跨年度零样本评价的动机一致：评价泛化能力时，应该单独隔离出"训练期完全未见过的新实体/新家族”子集，而不能只看整体的跨时间平均指标（整体指标可能被"训练期已见过、未来又重复出现”的样本拉高）。

## 局限

- 与 ECML 版共享同一批局限：固定 10 流子序列窗口、良性流量混入正类 bag 造成标签噪声、依赖能力受限的中间人解密收集训练标签。
- 数据规模明显小于扩展版，正类比例（3.26%/6.5%）与扩展版（0.81%/0.64%）差异较大，说明两篇论文的数据集并非同一批数据的子集关系，而是不同时间点/不同收集范围的独立采集，直接比较两篇论文的绝对数字需谨慎。
- 论文没有报告未知哈希子集在"跨主机/跨网络"维度上的进一步细分。

## 逐字引文

> "the LSTM model outperforms the random forest, and that the combination of neural domain-name features and flow features outperforms either of these feature sets" —— 第 209 页（Section 7.2 实验结论）。

## 文献信息

- 会议：2017 IEEE Security and Privacy Workshops (SPW)，DOI 10.1109/SPW.2017.8，第 205–210 页。
- 扩展版：见 [[2017-Prasse-加密流量LSTM恶意软件检测-ECML]]（ECML PKDD 2017）。
