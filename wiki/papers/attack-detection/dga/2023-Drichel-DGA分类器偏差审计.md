---
schema: paper-note-search/v1
title: "False Sense of Security: Leveraging XAI to Analyze the Reasoning and True Performance of Context-less DGA Classifiers"
title_zh: "安全错觉：用可解释人工智能审计无上下文DGA分类器"
authors: [Arthur Drichel, Ulrike Meyer]
year: 2023
date: 2026-09-07
journal: "RAID 2023"
doi: "10.1145/3607199.3607231"
arxiv_id: "2307.04358"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2023-Drichel-False-Sense-Security-DGA.pdf]]"
tags: [DGA检测, 偏差, XAI, 时间泛化, 低误报, 类型/论文]
aliases: [Drichel2023, False Sense of Security DGA]
tasks: [DGA二分类, 家族多分类, 偏差审计, 跨网络时间评价]
datasets: [DGArchive, 大学NXD, 企业311M NXDs]
methods: [B-ResNet, M-ResNet, EXPLAIN, 偏差约简并行分类]
metrics: [TPR, FPR, PR-AUC, 宏F1]
key_finding:
  - "去除TLD、无效域名、长度和时间/空间偏差后，e2LD二分类在默认阈值只有TPR 0.89139、FPR 0.10544（PDF物理第9至11页，表2）。"
  - "跨网络17个月、311M良性e2LD的最坏情形平均TPR 0.85735、FPR 0.00506；FPR 0.001至0.002时TPR约0.67至0.78（PDF物理第12至13页）。"
supports: ["99.9%静态高分可能来自TLD/长度/数据构造捷径", "低FPR和真实基率必须进入C00评价"]
cannot_support: ["无上下文分类器单独完成Botnet检测", "低FPR下未见家族已解决"]
related: ["[[2020-Drichel-DGA分类器真实适用性]]", "[[2021-Drichel-EXPLAIN多类DGA]]", "[[2024-Cebere-DGA检测九项假设审计]]"]
---

# DGA 分类器偏差审计

> 页码锚点：本地PDF共16页；偏差发现见 PDF 物理第7至10页，偏差约简和真实评价见 PDF 物理第10至13页。

## 一句话

该文直接否定“静态99.9%准确率意味着问题已解决”，并给出偏差约简、真实基率、低FPR和未知家族下的大幅退化。

## 论文可以支持

- C00必须经过TLD/长度/无效域名、时间、网络和基率审计。
- 低FPR下的真实 TPR 是比默认阈值 F1 更强的主指标。

## 论文不能支持

- 不能证明其并行偏差约简系统在DRIFT上有效。

## 实验结果与负证据

- 静态B-ResNet ACC 0.99864、FPR 0.00255；偏差约简e2LD默认阈值FPR升到0.10544。
- 真实最坏情形平均TPR 0.85735、FPR 0.00506；Nymaim2新家族TPR仅14.84%。
- 两个被标为不同家族的Ud4/Dmsnif实际生成完全相同域名，说明家族名隔离必须下沉到生成器/重复簇。

## 与本课题的关系

B-ResNet应与DRIFT双分支并列候选C00；任何条件记忆或家族稳健风险必须在偏差约简后的低FPR/未见家族分面改善。

## 文献信息

- <https://arxiv.org/abs/2307.04358>
