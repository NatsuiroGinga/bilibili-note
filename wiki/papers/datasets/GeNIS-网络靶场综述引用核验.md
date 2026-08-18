---
title: "GeNIS 在网络靶场技术综述中的引用核验"
authors:
  - Klaus Mayer
  - Max Landauer
  - Florian Skopik
  - Markus Wurzenberger
year: 2026
date: 2026-08-12
journal: "International Journal of Information Security 25:140"
source_pdf: "[[raw/papers/datasets/2026-Mayer-Engineering-cyber-ranges-survey.pdf]]"
doi: "10.1007/s10207-026-01298-y"
tags:
  - 网络靶场
  - GeNIS
  - 系统综述
  - 引用核验
  - 类型/论文
aliases:
  - Mayer2026-CyberRangesSurvey
  - GeNIS B类引用
key_finding: "该系统综述只把 GeNIS 作为 Airbus CyberRange 生成网络入侵数据的技术实例，没有使用 GeNIS 样本训练或评价模型，因此属于 B 类引用而非实际实验使用。"
---

# GeNIS 在网络靶场技术综述中的引用核验

> B 类引用论文；109 页正式开放全文，CC BY 4.0。

## 一句话

全文只用 GeNIS 说明云端网络靶场可以生成企业拓扑中的攻击、良性与背景流量，没有下载或使用其数据做实验。

## 综述范围

- 论文系统回顾 2020 年至 2025 年 8 月的 199 篇文献，整理 650 种技术、10 个技术域和 81 个技术子域，分析网络靶场与安全测试床的用例、基础设施和技术趋势（PDF 第 1、4–5 页）。
- 该综述的研究问题聚焦平台用例、技术组件和发展趋势，不是入侵检测模型比较（PDF 第 2、4 页）。

## GeNIS 引用位置与分类

- 正文在 PDF 第 25 页指出，GeNIS 是利用 GECAD 可用的 Airbus CyberRange 云端网络仿真基础设施开发的数据集，该平台生成企业拓扑中的攻击者恶意流、合法用户良性流和背景流量。
- 参考文献第 166 项在 PDF 第 107 页给出数据论文及 DOI `10.1016/j.dib.2025.111487`。
- 全文没有 GeNIS 数据版本、样本数、字段、拆分、模型、指标或实验结果。因此分类为 **B：方法/平台综述引用**，不得计入 GeNIS 实际使用论文基线。

## 证据边界

- 可以支持：GeNIS 被后续网络靶场综述作为 Airbus CyberRange 数据生成案例引用。
- 不能支持：任何 GeNIS 分类精度、泛化能力、字段选择或可复现性结论。

## 文献信息

- DOI：<https://doi.org/10.1007/s10207-026-01298-y>
- 本地 PDF SHA-256：`4d7a07dda03707fff2192f28f300f46617608291190a7598021bb48dd6227df1`

