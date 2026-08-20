---
schema: paper-note-search/v1
title: "Curriculum Learning"
title_zh: "课程学习"
authors:
  - "Yoshua Bengio"
  - "Jérôme Louradour"
  - "Ronan Collobert"
  - "Jason Weston"
year: 2009
date: 2026-08-20
journal: "Proceedings of ICML"
doi: null
arxiv_id: null
source_pdf: "[[raw/papers/methodology/2009_Bengio_Curriculum_Learning.pdf]]"
fulltext_verified: true
aliases:
  - "课程学习"
tasks:
  - "非凸模型训练"
datasets:
  - "论文内实验数据集"
methods:
  - "课程学习"
metrics:
  - "测试误差"
tags:
  - "类型/论文"
  - "主题/课程学习"
key_finding:
  - "训练分布可从易样本偏置逐步回到目标分布"
supports:
  - "课程顺序可以作为训练机制"
cannot_support:
  - "课程学习必然改善泛化"
related:
  - "[[wiki/papers/methodology/2009-Bengio-课程学习]]"
---

# Curriculum Learning

> 这是 `paper-note-search/v1` 的可执行结构示例。复制后必须替换全部题录、原件、论断和页码，不能把示例内容沿用到其他论文。

## 论文可以支持

- 论文在印刷 p.1 提出按有意义顺序组织训练样本的课程学习框架。

## 论文不能支持

- 论文不能支持课程学习在任意任务上必然提升，也不能支持使用测试标签定义难度。

## 实验结果与负证据

- 实验结果必须回到 PDF p.4 的对应表格核验；本示例不转录数值。

## 公式与页码

- 记录公式时同时写式号、印刷页和 PDF 页，例如“式（1），印刷 p.2，PDF p.2”。

## 与本课题的关系

- 可作为训练顺序机制来源，具体难度轴仍须由本课题数据和独立实验确定。
