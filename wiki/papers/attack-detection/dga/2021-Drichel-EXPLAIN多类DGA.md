---
schema: paper-note-search/v1
title: "First Step Towards EXPLAINable DGA Multiclass Classification"
title_zh: "迈向可解释DGA多类分类的第一步"
authors: [Arthur Drichel, Nils Faerber, Ulrike Meyer]
year: 2021
date: 2026-09-07
journal: "ARES 2021"
doi: "10.1145/3465481.3465749"
arxiv_id: "2106.12336"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2021-Drichel-EXPLAIN-DGA-Multiclass.pdf]]"
tags: [DGA检测, 随机森林, 可解释性, 多类分类, 类型/论文]
aliases: [EXPLAIN, Drichel2021]
tasks: [DGA家族多分类]
datasets: [DGArchive, 真实网络NXD]
methods: [EXPLAIN, 76项特征, 一对其余随机森林]
metrics: [宏平均F1, Precision, Recall, 每秒域名数]
key_finding:
  - "EXPLAIN-OvRUnion使用76项语言、统计与结构特征；精简RFE-PI版本用28项特征，最快版本约7812域名/秒（PDF物理第5至12页）。"
  - "后续同数据复现给出EXPLAIN宏F1 0.76733，接近M-ResNet 0.78682，说明可解释特征模型不是弱基线。"
supports: ["EXPLAIN是多类家族归因的强可解释基线", "等容量深度模型应超过强特征模型"]
cannot_support: ["二分类低FPR", "时间外推", "未见家族"]
related: ["[[2020-Drichel-DGA分类器真实适用性]]", "[[2023-Drichel-DGA分类器偏差审计]]"]
---

# EXPLAIN 多类 DGA 分类

> 页码锚点：本地PDF共13页。MinerU精确与快速模式均失败；本轮以Zotero附件 `THAUE8Q7` 的68,024字符索引全文和 PDF 物理第1至13页复核。

## 一句话

EXPLAIN 用强人工特征和随机森林逼近深度多类模型，证明传统方法不能被故意弱化。

## 论文可以支持

- 家族多分类至少应有 EXPLAIN 或等价强特征基线。

## 论文不能支持

- 不能支持跨年二分类 C00，也不提供固定低 FPR 结果。

## 实验结果与负证据

- 最强配置76项特征；精简配置28项特征。
- 后续偏差审计显示补充少量被筛掉特征可改善特定家族，但不能消除分布偏差。

## 与本课题的关系

若第三章只做二分类，EXPLAIN进入已发表谱系表但不是必跑C00；若报告家族归因，则必须进入正式比较。

## 文献信息

- <https://arxiv.org/abs/2106.12336>
