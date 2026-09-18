---
schema: paper-note-search/v1
title: "McNdroid: A Longitudinal Multimodal Benchmark for Robust Drift Detection in Android Malware"
title_zh: "McNdroid：Android恶意软件鲁棒漂移检测的长期多模态基准"
authors: [Md Mahmuduzzaman Kamol, Jesus Lopez, Saeefa Rubaiyet Nowmi, Emilia Rivas, Md Ahsanul Haque, Edward Raff, Aritran Piplai, Mohammad Saidur Rahman]
year: 2026
date: 2026-09-08
journal: "arXiv 2605.06894v1（2026-05-07，预印本）"
doi: null
arxiv_id: "2605.06894"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/drift/2026-Kamol-McNdroid-Multimodal-Android-Malware-Drift.pdf]]"
tags:
  - Android恶意软件
  - 多模态
  - 概念漂移
  - 时间泛化
  - 数据集
  - 类型/论文
tasks: [Android恶意软件二分类, 多模态融合, 时间泛化, 概念漂移]
datasets: [McNdroid, LAMDA]
methods: [静态特征, 动态特征, 函数调用图, 多模态融合, 源期词表]
metrics: [F1, ROC-AUC]
key_finding:
  - "McNdroid 把 LAMDA 直接列为最近基准，并以 858,859 个跨 12 年 APK 的静态、动态和调用图对齐视图补足其静态单模态边界。"
  - "论文明确只用 2013 训练分片构建词表，为修复 LAMDA 的未来协变量预处理提供直接协议近邻。"
supports: [LAMDA静态单模态边界, 源期专属词表协议, SHA256去重和跨模态一致性检查]
cannot_support: [已经重算LAMDA表7, 固定动态向量天然适合RWKV, 多模态融合在所有划分均占优]
method: "静态、动态、函数调用图三模态对齐，严格时间切分，多模态融合与漂移评估"
baseline: "MLP、LightGBM、XGBoost、SVM、DetectBERT、Transformer；早期/后期/交叉注意力融合"
aliases:
  - McNdroid
  - Kamol2026-McNdroid
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
---

# McNdroid：LAMDA 的多模态直接扩展

> 页码锚点：标题位于 PDF 物理第 1 页；本轮按第 2–4 节、表 1–2 核验，精确物理页待 MinerU 分页输出修复后补。

## 证据与题录

- arXiv `2605.06894v1`，2026-05-07，当前为预印本。
- 本地 PDF SHA-256 `a61619af595c8b97f0eeebb93488daff78c387d1060922731d05c36539f8da14`。
- MinerU 快速接口因 26 页拒绝；按页段重试时服务无错误退出但未生成文件。本笔记使用 arXiv 官方 HTML 全文，表号可核，PDF 页码待补。
- Zotero：`23DE8377`，题录已导入，未自动附加 PDF。

## 与 LAMDA 的直接关系

- 第 2 节明确称 LAMDA 是“最近的相关基准”，但只提供 Drebin 式静态特征，无法区分静态伪迹、运行时行为、程序结构和家族变化各自造成的退化。
- McNdroid 与 LAMDA 共享 2013–2025、缺 2015 的时间范围与弱标签思路，并引用 LAMDA 作为协议来源。
- 表 1：McNdroid 858,859 个样本、1,354 个家族、静态/动态/图三模态；LAMDA 1,008,381 个样本、静态单模态。

## 修复性协议证据

- 第 3.2 节明确只用 **2013 训练分片**构建静态全局词表，再以 `VarianceThreshold(0.001)` 从 501,525 维降到 2,390 维。
- 函数调用图的敏感 API 词表同样只从训练数据构建；样本按 SHA-256 去重并检查跨模态哈希/标签一致性。
- 这不是对 LAMDA 表 7 的重新计算，但证明同一作者群在后续基准中采用了更严格的来源专属预处理合同。

## 结果与边界

- 表 2 中，IID 多模态融合通常小幅优于最佳单模态；NEAR 时各模型 F1 大幅下降，标准差很大。
- 发布的动态表示是固定 17,483 维特征，图表示是 2,793 维结构统计和敏感 API 指示，而不是天然的长事件序列。
- 因此 McNdroid 虽增加了行为模态，却仍不能仅凭“动态”二字证明 RWKV 必要；需要原始有序调用、顺序打乱和同预算序列基线。

## 论文可以支持

- LAMDA 的静态单模态不能定位运行时或程序结构漂移；源期词表是可执行的防泄漏协议。

## 论文不能支持

- 不能支持 RWKV 对发布的固定多模态向量具有结构必要性。

## 实验结果与负证据

- 多模态在 IID 常小幅领先，但 NEAR F1 仍显著退化且标准差大；复杂融合没有消除时间病灶。

## 与本课题的关系

- 首要用途是修复 LAMDA 预处理合同；动态/图模态只作为后续条件候选。

## Evidence Record

Evidence ID: `MCNDROID-E1`
Source: arXiv `2605.06894v1`
Source type: preprint | full paper | dataset
Supports: LAMDA 的静态单模态边界；源期专属词表和哈希去重的可执行协议
Contradicts: “跨年 benchmark 可以用全时期无标签特征共同拟合预处理”
Method / dataset / metric: 12 年三模态 Android APK；F1、ROC-AUC、时间切分
Limitation: 预印本；发布特征仍主要是固定向量
Project relevance: LAMDA 协议修复与 RWKV 软资格参照
Claim strength: supported

## 文献信息

- arXiv：https://arxiv.org/abs/2605.06894
- 数据：https://doi.org/10.5281/zenodo.19969833
