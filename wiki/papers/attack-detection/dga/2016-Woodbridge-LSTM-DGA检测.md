---
schema: paper-note-search/v1
title: "Predicting Domain Generation Algorithms with Long Short-Term Memory Networks"
title_zh: "使用长短期记忆网络预测域生成算法"
authors: [Jonathan Woodbridge, Hyrum S. Anderson, Anjum Ahuja, Daniel Grant]
year: 2016
date: 2026-09-07
journal: "arXiv preprint"
doi: null
arxiv_id: "1611.00791"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2016-Woodbridge-LSTM-DGA-Detection.pdf]]"
tags: [DGA检测, LSTM, Endgame, 低误报, 类型/论文]
aliases: [Woodbridge2016, Endgame LSTM]
tasks: [DGA二分类, DGA家族多分类, 留出家族检测]
datasets: [Alexa Top 1M, 30个DGA家族公开数据]
methods: [字符嵌入, 单层LSTM, 逻辑回归输出]
metrics: [ROC-AUC, F1, TPR@FPR]
key_finding:
  - "静态十折交叉验证报告二分类AUC 0.9993、多分类微F1 0.9906，并给出TPR 90%时FPR 0.0001（PDF物理第1、10至12页）。"
  - "十个最小家族被整体移出训练以测试新家族，但该实验仍使用同一时期和同一数据构造，不等于未来年份泛化（PDF物理第8至11页）。"
supports: ["Endgame/LSTM是必须保留的历史字符序列基线", "低FPR工作点应显式报告"]
cannot_support: ["时间外推稳健性", "跨年重复隔离", "现代DGArchive/Tranco协议下的性能"]
related: ["[[2018-Yu-字符级DGA模型比较]]", "[[2020-Drichel-DGA分类器真实适用性]]", "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"]
---

# Woodbridge LSTM DGA 检测

> 页码锚点：本地 PDF 共13页；数据与实验设计见 PDF 物理第7至9页，结果见 PDF 物理第10至12页。

## 一句话

以原始域名字符输入的浅层 LSTM 建立了 Endgame 基线，并首次把 `TPR@FPR=10^-4` 作为实用证据，但其高分来自静态交叉验证。

## 论文可以支持

- 字符 LSTM 无需人工特征即可做单域名实时检测。
- 低误报工作点比准确率更贴近网关部署。

## 论文不能支持

- 不能证明跨年份或跨网络稳健，也没有实体去重和种子不确定性。

## 实验结果与负证据

- 二分类使用30个家族和 Alexa，十折交叉验证；AUC 0.9993。
- 90% TPR 时 FPR 0.0001；多分类微 F1 0.9906。
- 宏平均被作者认为更适合不均衡家族，但主要结论仍来自微平均。

## 与本课题的关系

Endgame 应进入已发表最低比较集，但必须按 DRIFT 的冻结年份、重复排除和同预算重新训练，不能搬用 2016 数字。

## 文献信息

- <https://arxiv.org/abs/1611.00791>
