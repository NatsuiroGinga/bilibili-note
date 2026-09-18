---
schema: paper-note-search/v1
title: "Down to Earth! Guidelines for DGA-based Malware Detection"
title_zh: "脚踏实地：DGA恶意软件检测指南"
authors: [Bogdan Cebere, Jonathan Flueren, Silvia Sebastian, Daniel Plohmann, Christian Rossow]
year: 2024
date: 2026-09-07
journal: "RAID 2024:147-165"
doi: "10.1145/3678890.3678913"
arxiv_id: null
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2024-Cebere-Down-to-Earth-DGA-Guidelines.pdf]]"
tags: [DGA检测, 系统综述, 数据泄漏, 未见家族, 可复现性, 类型/论文]
aliases: [Down to Earth DGA, Cebere2024]
tasks: [DGA检测方法审计, 实验与部署假设审计]
datasets: [Tranco, DGArchive, 对抗和词典型DGA]
methods: [38篇contextless论文元审计, 九项假设实证复核]
metrics: [F1, MCC, 家族敏感性, 推理开销]
key_finding:
  - "38篇无上下文DGA论文中，只有26%明确支持未见家族假设，64%不支持，10%口径不清；共享底层生成器会制造伪未见家族（PDF物理第13至14页，A9）。"
  - "只有6篇公开代码，没有一篇提供精确评价数据、随机种子与抽样策略，跨论文高分不可直接比较（PDF物理第15页，4.2节）。"
supports: ["良性污染清理、家族支持敏感性、生成器级隔离和推理开销是强制门", "DGA检测不等于完整Botnet检测"]
cannot_support: ["任一具体模型在DRIFT上有效", "Tranco或DGArchive天然无污染"]
related: ["[[2023-Drichel-DGA分类器偏差审计]]", "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"]
---

# DGA 检测九项假设审计

> 页码锚点：本地PDF共19页；九项假设见 PDF 物理第6至14页，讨论和复现结论见 PDF 物理第15至16页。

## 一句话

该文系统说明大多数contextless DGA研究依赖脆弱的数据、威胁和部署假设，是本课题评价合同的最高优先级方法学来源。

## 论文可以支持

- A5要求清理良性污染；A6要求家族支持敏感性；A9要求真正未见生成器。
- 单一平均值、无代码、无精确样本清单不能形成可复现天花板。

## 论文不能支持

- 不能据元审计直接淘汰字符串模型；它要求更严格实验而非预判结果。

## 实验结果与负证据

- 审计54篇DGA检测论文，其中38篇contextless；九项假设覆盖问题、实验和部署。
- 只有6篇公开代码，且没有精确评价数据、种子与抽样策略。
- DGA家族名不同不保证底层生成器不同，必须做生成器/重复簇隔离。

## 与本课题的关系

第三章数据门、C00和所有机制实验都应显式执行A5/A6/A9，不以DRIFT官方划分自动代替。

## 文献信息

- DOI `10.1145/3678890.3678913`。
