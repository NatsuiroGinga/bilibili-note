---
schema: paper-note-search/v1
title: "Dom2Vec - Detecting DGA Domains through Word Embeddings and AI/ML-driven Lexicographic Analysis"
title_zh: "Dom2Vec：结合词嵌入与词法分析的DGA检测"
authors: [Lucas Torrealba Aravena, Pedro Casas, Javier Bustos-Jimenez, Guillermo Capdehourat, Mislav Findrik]
year: 2023
date: 2026-09-07
journal: "19th International Conference on Network and Service Management"
doi: "10.23919/CNSM59352.2023.10327913"
arxiv_id: null
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2023-Aravena-Dom2Vec-DGA.pdf]]"
tags: [DGA检测, Word2Vec, ngram, 随机森林, 低误报, 类型/论文]
aliases: [Dom2Vec, Aravena2023]
tasks: [DGA二分类]
datasets: [Alexa 337500, Netlab 25个DGA家族]
methods: [RVP ngram信誉分, 词法特征, Dom2Vec 503维表示, 随机森林]
metrics: [ROC, TPR@FPR]
key_finding:
  - "平衡675000域名、五折交叉验证中，Dom2Vec在FPR 1%时TPR 86%，比RF3高32个百分点（PDF物理第4页，图5）。"
  - "RVP对gozi、suppobox、nymaim、matsnu等词典型DGA明显失效，词嵌入主要补这一缺口。"
supports: ["词典型DGA需要子词/词义表示", "低FPR应报告TPR"]
cannot_support: ["跨年泛化", "未见家族", "条件记忆效果"]
related: ["[[2024-Lee-中文域低误报DGA检测]]", "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"]
---

# Dom2Vec

> 页码锚点：本地PDF共5个物理页；方法见第2至3页，数据和结果见第4页。

## 一句话

Dom2Vec 证明词典型 DGA 需要比固定 n-gram 更丰富的词表示，但只在静态平衡随机划分上验证。

## 论文可以支持

- n-gram信誉分、词法特征和词嵌入是DRIFT子词支路的直接前身。

## 论文不能支持

- 不能支持未来年份、未见家族或低于1% FPR的稳定性。

## 实验结果与负证据

- FPR 1%时TPR 86%；FPR 5%时接近95%。
- 数据以Alexa为良性、平衡抽样、五折交叉验证，没有重复实体和时间隔离。

## 与本课题的关系

普通词嵌入与词法组合已被占用；条件记忆只有超过Dom2Vec式静态表示和等容量对照才有差量。

## 文献信息

- [IFIP全文](https://dl.ifip.org/index.html/db/conf/cnsm/cnsm2023/1570935678.pdf)
