---
title: "LSPR23 仅作背景引用：KRONOS-SDN 未知攻击检测实验"
authors:
  - Francesco Di Gennaro
  - Andrea Giuliani
  - Christian Morbidoni
  - Alessandro Cucchiarelli
  - Luca Spalazzi
year: 2026
date: 2026-08-11
journal: "Joint National Conference on Cybersecurity（ITASEC & SERICS 2026），CEUR-WS Vol. 4198"
source_pdf: "[[raw/papers/datasets/LSPR24/2026_DiGennaro_Hierarchical_Hybrid_SDN_IDS.pdf]]"
tags:
  - LSPR23
  - KRONOS-SDN
  - 软件定义网络
  - 未知攻击检测
  - 排除核验
  - 类型/论文
key_finding: "全文只在相关工作中把 LSPR23 列为传统入侵检测基准；所有实验均使用 KRONOS-SDN 的 Open 交换机子集，因此该研究属于 B 类引用而非 LSPR23 直接使用论文。"
method: "一维卷积神经网络与多层感知机自编码器的两阶段层次框架，采用逐攻击留一法在 KRONOS-SDN 上评价未知攻击检测。"
baseline: "KRONOS-SDN 上的监督卷积神经网络、异常自编码器及两阶段组合；不含 LSPR 模型结果。"
aliases:
  - DiGennaro2026-LSPR23仅引用
  - KRONOS-SDN未知攻击检测
related:
  - "[[papers/datasets/LSPR24/Dijk-2024-LSPR23数据集与随机森林复现|LSPR23 数据集与随机森林复现]]"
  - "[[papers/datasets/INDEX|恶意流量数据集论文索引]]"
---

# LSPR23 仅作背景引用：KRONOS-SDN 未知攻击检测实验

## 分类结论

**B 类：只引用／介绍，不直接使用 LSPR23。**

- PDF 第 3 页第 2.1 节仅把 LSPR23 与 CICIDS2017、UNSW-NB15、CSE-CIC-IDS2018 并列为传统入侵检测基准，并指出这些数据不是软件定义网络数据、缺少控制器可见性。
- 同一段随即明确写明“我们在实验中采用 KRONOS-SDN”。
- 摘要、方法第 3.2 节、预处理第 3.3 节和全部结果均只使用 KRONOS-SDN；没有读取、训练、测试、统计或转换 LSPR23。
- 因此它不能计入 LSPR23／24／25 的 A 类直接使用论文，也不能给当前 LSPR 跨年方案提供可比较数字。

## 该文实际实验对象

- 数据：KRONOS-SDN 的流级 CSV，只取 `Open` 虚拟交换机一周流量。
- 任务：已知攻击监督检测加未知攻击异常检测，逐攻击类别留一模拟实验意义上的“零日”。
- 模型：一维卷积神经网络作为第一阶段，多层感知机自编码器只在正常流上训练并作为第二阶段。
- 子集：129,791 条正常流以及 `Open` 网段各攻击活动的全部流；随后执行类别上限和比例欠采样。
- 这些方法和结果只支持 KRONOS-SDN 上的结论，不应迁移成 LSPR 结果。

## 论文原结论

- 作者认为监督一维卷积神经网络与只在正常流上训练的多层感知机自编码器组成的两阶段框架，可改善 KRONOS-SDN 留一攻击评价中的未知攻击召回，同时保持稳定的良性流假阳性率。
- 这个结论的证据域是 KRONOS-SDN 的 `Open` 交换机子集，不包含 LSPR23。

## 本课题推论、可迁移机制与不可直接声称

- 本课题只把该文作为“题名或引用链命中不等于直接使用”的排除证据。
- 两阶段监督／异常检测结构可作为一般方法近邻，但是否适用于 LSPR 跨年冷启动仍待独立实验，不能由本论文结果推得。
- 不可把其 KRONOS-SDN 指标写成 LSPR23 基线，也不可把“未知攻击”直接等同于当前年度跨移任务。

## 原件与开放许可

- 官方全文：<https://ceur-ws.org/Vol-4198/paper53.pdf>。
- 会议：Joint National Conference on Cybersecurity（ITASEC & SERICS 2026），2026-02-09 至 2026-02-13。
- 许可：CC BY 4.0，正文首页明确标注。
- 本地原件：`raw/papers/datasets/LSPR24/2026_DiGennaro_Hierarchical_Hybrid_SDN_IDS.pdf`，15 页，1,374,016 字节。
- SHA-256：`7951ed4c6dff0d41222ecc6e6aa3d4e64815ed0b1fc10563f8931e06cf0dbb73`。
- 2026-08-11 已检查 PDF 元数据，提取全文，并渲染核对首页和第 3 页的 LSPR23 引用段。

## Evidence Record

- Evidence ID: ER-20260811-digennaro-lspr23-exclusion-01
- Source: Di Gennaro 等 2026 正式全文，PDF 第 1、3 至 5 页
- Source type: full paper
- Supports: LSPR23 只作为相关工作中的传统基准；实际实验仅用 KRONOS-SDN
- Scope: LSPR 直接使用论文查全审计的排除判定
- Verified: 2026-08-11
- Verifier: Codex
- Claim strength: supported

## Zotero

- Zotero 条目键：`VRA8LK86`。
- 连接器从 CEUR 官方 PDF 导入，并建立 PDF 子附件 `DCRYX3U8`；因页面没有 DOI，父条目被连接器保存为网页类型，正式题录仍以 CEUR 全文和本笔记为准。
