---
title: "Malware Detection by Analysing Encrypted Network Traffic with Neural Networks"
authors: [Paul Prasse, Lukáš Machlica, Tomáš Pevný, Jiří Havelka, Tobias Scheffer]
year: 2017
date: 2026-08-13
journal: "ECML PKDD 2017"
source_pdf: "[[raw/papers/methodology/multiple-instance/2017-Prasse-Malware-Detection-Encrypted-Network-Traffic-Neural-Networks-ECML.pdf]]"
sha256: "38cf4e7771d01ab93531825bb6823d4463538fa7d89f2ac9aa1bd7c15eadbb6e"
tags:
  - 加密流量检测
  - LSTM
  - 弱标注
  - 类型/论文
key_finding: "把每个客户端每 24 小时的 HTTPS 流量切成固定长度 10 条流的子序列，任一子序列中出现恶意应用的流量即标注该子序列为正，用 LSTM 处理（流特征+域名神经嵌入），日级判定取所有子序列打分的最大值；正类信号极稀疏（当前数据 350,220/43,150,605 条流为恶意，约 0.81%），且论文明确讨论了'良性应用流量会干扰恶意模式'的实例级弱标注问题。"
method: "客户端×24小时为分类实例，实例内按 10 条流切子序列（bag），子序列内任一流恶意则子序列标注为正；每条流特征=时长/收发字节对数变换+域名神经嵌入（CBOW 训练的 100 维向量）；LSTM（32 单元）+128 ReLU+softmax 处理子序列，日级得分取全部子序列最大激活。"
baseline: "随机森林（相同特征堆叠）；域名特征消融对比：60 维人工工程特征 vs. 字符 2-gram vs. 神经嵌入"
aliases:
  - Prasse2017-ECML
  - Prasse2017-加密流量LSTM
related:
  - "[[2017-Prasse-网络流量LSTM恶意软件检测-SPW]]"
---

# Malware Detection by Analysing Encrypted Network Traffic with Neural Networks

> Prasse, Machlica, Pevný, Havelka, Scheffer, ECML PKDD 2017（欧洲机器学习与知识发现数据库大会）。是同作者 2017 IEEE S&P Workshop 论文的扩展版（正文明确说明"we have presented some of the results of this paper to a computer-security audience in a prior workshop paper”，即 [[2017-Prasse-网络流量LSTM恶意软件检测-SPW]]）。

## 一句话

在无法看到 HTTP payload/URL 的 HTTPS 流量上，只用可观测的主机地址、时间戳、数据量和（若可见）域名信息，把每个客户端每天的流量切成 10 条流一组的子序列喂给 LSTM，训练信号是"子序列内任一流是否来自恶意应用”的弱标注；论文用大规模真实企业流量（现刊数据 4400 万条流）验证了该方法对未来两个月流量、未知恶意软件家族的检测能力。

## 序列构造与聚合层级

- **分类实例粒度**：客户端 × 24 小时（即"逐用户/逐实体—按天"，不是逐流也不是跨天聚合单一用户）。同一客户端在多天活跃则产生多个独立分类实例（Section 4，"Client Malware Detection Problem"）。
- **标注方式**：实例（一天的全部流量）中，只要有至少一个流来自恶意应用即标正；只有良性应用流量则标负。**同一实例内会混合多个应用（含良性应用）的流量**——论文明确指出"benign applications will generally interfere with any patterns in the malware's communication"（Section 5.1），承认这是一种带噪声的弱监督设置。
- **序列切分**：LSTM 和随机森林都把客户端流量固定切成 **10 条流一组的子序列**（Section 5.3）；训练时子序列标签＝子序列内是否存在恶意流（OR 聚合）；推断时，实例（一天）的最终得分＝该实例内**所有相邻 10 流子序列**打分的**最大值**（sliding max）。这是一个两层的多实例学习结构：实例（天）是子序列的 bag，子序列又是流的 bag，标签沿两层都用"至少一个为正即正”传播。
- **标签来源**：VPN 客户端记录发起流量的可执行文件 SHA 哈希，上传 VirusTotal 用 60 个杀毒引擎判定；≥3 个引擎判恶意才标正，0 个标良性，1–2 个标"不确定”并在训练/评价中跳过（Section 3.1）。Table 1（标签稳定性混淆矩阵）显示 5–7 个月后重新查询，仅 0.16% 的原恶意样本会翻转为良性，标注相对稳定。

## 正类比例与评价指标

- **数据规模与正类比例（流级别）**：current data（2016年7月，5天，171个网络）共 44,348,879 条流，20,130 个不同可执行文件哈希，其中 350,220 条恶意流 / 43,150,605 条良性流，恶意流占比约 **0.81%**；future data（2016年9月，8天，169个网络）149,005,149 条流中 955,037 条恶意，约 0.64%。论文正文没有直接给出**实例级（客户端-天）**的正类比例数字，未在原件中定位。
- **评价指标**：Precision-Recall 曲线（主指标，因为 PR 曲线随类别比变化更直接反映应用价值）、ROC 曲线（类别比不变时的补充指标，横轴对数刻度）、特定精度下的召回率 R@x%P、平均检测时延（首个恶意流到触发告警的时间间隔）。
- **关键数字**：Table 3（域名特征对比）：神经域名嵌入 R@70%P=0.84、R@80%P=0.79、R@90%P=0.73，均优于字符 2-gram（0.83/0.76/0.62）和 60 维人工工程特征（0.68/0.36/0.0）；神经+工程特征组合反而更差（0.75/0.64/0.24），论文认为工程特征"inflate the feature space while not adding a substantial amount of additional information"。Figure 2/3 显示 LSTM 全面优于随机森林，"neural+flow" 组合特征优于任一单一特征集。Table 5：跨时间平均检测时延 current 1.65–1.67 小时、future 1.36–1.40 小时（依阈值而异）。

## 我的理解 / 与本课题的关系

这篇论文示范了"实体×固定时间窗口（天）"这一聚合粒度下的弱监督多实例学习范式：正类信号来自极少数流量（<1%），标签沿多层 bag 结构传播（流→10流子序列→天），且显式承认良性流量会干扰正类模式识别。这与本课题"2-IP 实体级聚合后 AP 显著高于逐流"的现象在方向上一致——聚合到更粗粒度、跨越更长观测窗口，能让稀疏的恶意信号更容易被聚合层捕捉到，但也带来了标签噪声（bag 内良性事件被强行赋予正标签）的代价，这一权衡在本文里被明确讨论而不是回避。

## 局限

- 序列长度固定为 10 条流（截断/滑窗），未讨论更长历史或跨天累积上下文。
- 正类比例、评价均以"客户端"为实体，未讨论"主机对"或"IP 对"级别的聚合。
- 依赖 VirusTotal 多数投票标注，存在已知的标签噪声（Table 1 混淆矩阵量化了约 0.16%–10% 的翻转率，视原始标注置信度而定）。
- 训练数据依赖能中间人解密 HTTPS 的 CWS 服务，只对"配置了拦截”的一部分客户端可行，存在选择偏差风险；论文未讨论这一点是否影响标签代表性。

## 逐字引文

> "benign applications will generally interfere with any patterns in the malware's communication" —— Section 5.1（Flow Features，讨论实例内多应用混合流量的弱监督问题）。

## 文献信息

- 会议：ECML PKDD 2017。
- 相关技术报告：Prasse et al., "Malware detection by HTTPS traffic analysis", urn:nbn:de:kobv:517-opus4-100942 (2017)。
- 前置工作坊论文：见 [[2017-Prasse-网络流量LSTM恶意软件检测-SPW]]。
