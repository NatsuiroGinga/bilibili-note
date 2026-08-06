---
title: "When a RF Beats a CNN and GRU, Together—A Comparison of Deep Learning and Classical Machine Learning Approaches for Encrypted Malware Traffic Classification"
authors: [Adi Lichy, Ofek Bader, Ran Dubin, Amit Dvir, Chen Hajaj]
year: 2023
date: 2026-08-06
journal: "Computers & Security"
source_pdf: "[[raw/papers/attack-detection/encrypted/2022-Lichy-RF-Beats-CNN-GRU-Encrypted-Malware.pdf]]"
tags:
  - 加密恶意流量检测
  - 模型比较
  - 未知家族
  - 类型/论文
key_finding: "在统一数据折和多类任务下，随机森林可达到或超过复杂深度模型；未知家族表现对具体家族与数据来源高度敏感。"
method: "统一预处理后比较决策树、随机森林、K近邻与四类深度模型，并覆盖二分类、家族分类、留一家族未知检测和逐步增类。"
baseline: "RF、DT、KNN、DeepMAL、MalDIST、M1CNN、M2CNN。"
zotero_key: "K8CMUVX5"
aliases:
  - Lichy2023-RFBeatsDL
---

# When a RF Beats a CNN and GRU, Together

## 一句话

论文提醒加密恶意流量研究不能默认深度模型优于传统模型；公平的同折比较和未知家族测试比单一随机划分成绩更重要。

## 问题与方法

- 构建 MTAB、USTCB、MUB 三个组合数据集，在相同数据折上比较传统机器学习与深度模型。
- 数据先移除不足 784 个载荷字节的会话、过滤噪声协议，再把良性样本下采样到与恶意样本各占 50%。
- 任务包括恶意/良性二分类、恶意家族多分类、留一家族未知检测和逐步增加家族数。

## 数据与划分

- 恶意流量来自 MTA 与 USTC-TFC2016；良性流量来自 StratosphereIPS、ISCX2016、BOA 与 USTC。
- 处理后 MTAB 约 2.9 万、USTCB 约 5.8 万、MUB 约 8.7 万会话。
- 主比较采用五折交叉验证，所有模型使用完全相同的数据折。
- 未知家族测试每次把一个家族整体作为测试集，其余家族连同良性样本组成训练集。
- 证据：PDF 第 3 页表 1-3 与第 3.2 节；第 5 页第 4 节；第 7 页第 4.3 节。

## 主要结果

- 二分类中 RF 与 MalDIST 最优，三套数据上二者差距最多约 0.1%；RF 在表 4 中达到约 99.6%-100% 的分类准确率。
- 家族分类中 RF 在三套数据与各指标上整体优于最佳深度模型 MalDIST；作者同时明确不把此结果推广为“应避免深度学习”。
- 未知家族检测高度不稳定：例如 USTCB 的 Cridex 上 RF 约 90%，MalDIST 约 0.6%；另一些家族则深度模型更好。
- 证据：PDF 第 4 页表 4；第 7-8 页第 4.1-4.4 节与图 4-5。

## 限制

- 五折交叉验证是在“数据级”完成，论文未证明按原始 PCAP、主机或时间隔离，仍可能存在同源相关性。
- 多来源拼接可能引入采集环境、协议占比和工具链捷径；论文自身发现同家族跨 MTA/USTC 迁移可跌至 0%。
- 平衡二分类与真实部署中的低基率场景不同。

## 与本课题的边界

- **论文原结论**：传统模型在若干加密恶意流量任务上能匹配或超过深度模型，未知家族结果依赖家族和数据集。
- **可迁移机制**：共同折、共同预算、传统强基线、留一组外推测试。
- **不可直接声称**：未知家族不等于未知加密协议，跨数据源失败也不能归因于加密层。
- **仍需验证**：把训练/测试隔离提升到采集单元后，模型排序是否改变。

## 文献信息

- DOI：[10.1016/j.cose.2022.103000](https://doi.org/10.1016/j.cose.2022.103000)
- arXiv：[2206.08004](https://arxiv.org/abs/2206.08004)
- Zotero 条目键：`K8CMUVX5`

