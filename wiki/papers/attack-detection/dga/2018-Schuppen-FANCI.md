---
schema: paper-note-search/v1
title: "FANCI: Feature-based Automated NXDomain Classification and Intelligence"
title_zh: "FANCI：基于特征的NXDomain自动分类与情报"
authors: [Samuel Schüppen, Dominik Teubert, Patrick Herrmann, Ulrike Meyer]
year: 2018
date: 2026-09-07
journal: "27th USENIX Security Symposium"
doi: null
arxiv_id: null
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2018-Schuppen-FANCI-DGA-Detection.pdf]]"
tags: [DGA检测, 随机森林, NXDomain, 低误报, 类型/论文]
aliases: [FANCI, Schuppen2018]
tasks: [恶意NXDomain二分类, DGA家族识别, 未见DGA检测]
datasets: [DGArchive 59家族, 大学网络NXD, 企业网络NXD]
methods: [21项结构语言统计特征, 九棵决策树随机森林]
metrics: [Accuracy, F1, TPR, FPR]
key_finding:
  - "FANCI只读取单个NXDomain的结构、语言与统计特征，并在大学和企业真实NXD数据上评估（PDF物理第1至13页）。"
  - "后续统一复现无法在不同良性数据上稳定建立0.1% FPR阈值，说明原始低误报依赖数据与后过滤协议。"
supports: ["传统特征随机森林是低成本强基线", "真实NXD良性样本比Alexa更贴近部署"]
cannot_support: ["任意解析域名流量", "跨年实体隔离", "深度模型必然优于特征模型"]
related: ["[[2020-Drichel-DGA分类器真实适用性]]", "[[2019-Peck-CharBot规避攻击]]", "[[2024-Cebere-DGA检测九项假设审计]]"]
---

# FANCI

> 页码锚点：USENIX正式页1165至1181，对应本地PDF物理第1至18页；数据与分类结果位于正文第4至6节。

## 一句话

FANCI 是单域名、真实 NXD、可解释随机森林基线，价值主要在部署口径而非静态最高分。

## 论文可以支持

- 真实网络 NXD 可服务低成本 DGA 检测与未知家族发现。
- 人工特征模型应作为神经网络的非弱化对照。

## 论文不能支持

- 不能把 NXDOMAIN 结果外推到已注册 DGA 或所有 DNS 请求。

## 实验结果与负证据

- 原文用59个 DGArchive 家族、大学和企业 NXD 数据。
- 跨数据复现显示阈值和后处理对低 FPR 影响很大，CharBot 在低 FPR 下可轻易绕过。

## 与本课题的关系

FANCI 不宜作为唯一 C00，但必须进入已发表比较表的传统方法列，并用同一 eSLD/年份协议重跑。

## 文献信息

- <https://www.usenix.org/conference/usenixsecurity18/presentation/schuppen>
