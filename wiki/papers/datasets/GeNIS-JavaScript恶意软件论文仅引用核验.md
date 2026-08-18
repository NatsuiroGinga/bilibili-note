---
title: "GeNIS 在 JavaScript 恶意软件合成数据论文中的仅引用核验"
authors:
  - Hind Ikni
  - Alaa Eddine Belfedhal
year: 2025
date: 2026-08-12
journal: "人工智能与创新应用国际会议（AIIA 2025）"
source_pdf: "[[raw/papers/datasets/citation-only/2025-Ikni-JavaScript-malware-synthetic-dataset.pdf]]"
doi: "10.1109/AIIA68273.2025.11383680"
tags:
  - JavaScript恶意软件
  - GeNIS
  - 合成数据
  - 引用核验
  - 类型/论文
aliases:
  - Ikni2025-JavaScriptSynthetic
  - GeNIS JavaScript B类引用
key_finding: "该文只在相关工作中把 GeNIS 作为通过仿真真实攻击场景采集网络流量的传统数据构建实例，实验全部使用合成 JavaScript 与 Sschumat 脚本，因此属于 B 类仅引用。"
---

# GeNIS 在 JavaScript 恶意软件合成数据论文中的仅引用核验

> B 类引用论文；IEEE AIIA 2025 正式 PDF，共 6 页。

## 一句话

GeNIS 只作为网络入侵数据集的传统构建方法示例出现，没有参与本文的 JavaScript 生成、训练或测试。

## GeNIS 的精确引用语境

- 相关工作在 PDF 第 2 页将 GeNIS 与另一数据集并列，说明网络入侵与异常检测数据常通过在受监控环境中模拟真实攻击场景来生成网络流量包；这种构建依赖具体物理或虚拟基础设施及其漏洞。
- 参考文献第 6 项在 PDF 第 6 页给出 GeNIS 数据论文书目信息。
- 这段话只讨论传统数据收集方法，没有使用 GeNIS 的文件、样本、字段、标签或结果。

## 本文真正使用的数据与任务

- 本文生成 9,780 个合成 JavaScript 片段，其中良性 5,480、恶意 4,300；用 CodeBERT 分类，并与 Sschumat 的真实 JavaScript 数据集做双向跨数据集评价（表 III–VI，PDF 第 4–5 页）。
- 训练/验证/测试为 70/15/15，任务、输入模态和标签均与网络流 GeNIS 无关（PDF 第 4–5 页）。

## 分类裁决

- **B 类：相关工作/数据构建方法引用。**
- 不得把该文计入 GeNIS 实际使用、检测基线或泛化结果。

## 文献信息

- DOI：<https://doi.org/10.1109/AIIA68273.2025.11383680>
- 本地 PDF SHA-256：`e8788fef603636ad1a6d7cfba632f84a1807d483d75d216a5195890bf63dcb35`

