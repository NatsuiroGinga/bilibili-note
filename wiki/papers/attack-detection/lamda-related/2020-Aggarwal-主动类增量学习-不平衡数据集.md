---
schema: paper-note-search/v1
title: "Active Class Incremental Learning for Imbalanced Datasets"
title_zh: "面向不平衡数据集的主动类增量学习"
authors: [Umang Aggarwal, Adrian Popescu, Eden Belouadah, Léo Saci]
year: 2020
date: 2026-10-15
journal: "ECML-PKDD 2020（Springer，DOI 10.1007/978-3-030-65414-6_12）；arXiv 2008.10968v1"
doi: "10.1007/978-3-030-65414-6_12"
arxiv_id: "2008.10968"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2020-Belouadah-主动类增量学习-不平衡数据集.pdf]]"
tags:
  - 持续学习
  - 主动学习
  - 类不平衡
  - 类型/论文
tasks: [类增量学习, 主动学习, 类不平衡]
datasets: [四个视觉数据集]
methods: [两阶段样本获取函数（标准 AF → 平衡驱动 AF）, 类预测缩放（推理期）, 微调基线]
metrics: [准确率]
key_finding:
  - "同时丢弃「新数据随到随标」与「测试集平衡」两个强假设，用主动学习+不平衡学习组合处理类增量（摘要原文）。"
  - "标注预算 B 分两阶段消耗：先用标准获取函数在部分预算上学更新模型，再用平衡驱动的获取函数补标（正文 §方法）；把 IL 当不平衡学习问题处理（推理期类预测缩放），而非知识蒸馏抗遗忘。"
supports: [类增量+标注预算+类不平衡三者共置的早期先例（视觉域）]
cannot_support: [存储受限设定（其方法用累积标注集∪K，无固定缓冲预算）, 漂移流式协议, 恶意软件域]
method: "两阶段获取函数 + 模型微调 + 类预测缩放"
baseline: "现有获取函数对比"
aliases:
  - Aggarwal2020-ACIL
related:
  - "[[2024-Park-PBR先验无关平衡回放]]"
---

# Aggarwal 等：主动类增量学习（不平衡数据集）

> 页码锚点：按 MinerU 转换件章节引用。证据等级：本地全文。arXiv v1 与 Springer 版署名顺序不同（arXiv 首列 Eden Belouadah，Springer 版首列 Umang Aggarwal），以 Springer 出版版为准。

## 一、协议与预算（与待核任务逐项对照）

- **标注预算**：有——预算 B 按「两阶段过程」分批消耗（§方法原文：先在部分预算上学中间模型，再用平衡驱动获取函数补标，重复 T 次直到 B 耗尽）。
- **存储预算**：无——引言讨论了「有界记忆回放」这一研究方向（原文引 [10,14,20,33,46]），但其自身方法把新标注样本累积进 K/已标注集，无固定缓冲与替换策略。
- **类不平衡**：核心轴之一——获取函数偏向多数类的问题用两阶段平衡驱动获取解决；推理期用类预测缩放。
- **协议与域**：视觉类增量（CIFAR/MNIST 系），无漂移流、非恶意软件、非 Domain-IL。

## 二、与目标任务的差量

占「标注预算 × 类不平衡 × 类增量」三轴，缺「固定存储预算」与「漂移序列」两轴；是不平衡主动学习进入增量情景的早期代表作（问题 2/3 证据），不构成双预算联合配置先例。

## 四、入库与 Zotero

- PDF：`raw/papers/attack-detection/lamda-related/2020-Belouadah-主动类增量学习-不平衡数据集.pdf`
- 全文转换件：`wiki/papers/attack-detection/lamda-related/2020-Aggarwal-主动类增量学习-不平衡数据集-全文.md`
- Zotero：本轮未导入。
