---
title: "MonroeQL 聚合性能数据及公开性边界"
authors: [Juan M. Ramírez, Fernando Díez, Pablo Rojo, Vincenzo Mancuso, Antonio Fernández-Anta]
year: 2023
date: 2026-08-03
journal: "Computer Communications 200"
source_pdf: "[[raw/papers/datasets/quic/Explainable-Machine-Learning-MonroeQL-2023.pdf]]"
tags:
  - QUIC
  - qlog
  - 性能异常
  - 数据集审计
  - 类型/论文
aliases:
  - MonroeQL
  - Ramirez2023-XMLAD
key_finding: "论文称 MonroeQL 由原始 qlog 聚合出 3951 个实验和 188 个 RTT、拥塞窗口、时长与吞吐特征，但官方仓未公开原始 qlog 或 MonroeQL 表，不能作为 R2 可复现数据源。"
---

# MonroeQL 聚合性能数据及公开性边界

## 一句话

MonroeQL 证明 qlog 可以生成有用的性能统计，但当前公开制品既缺原始数据，也缺完整逐包残差字段。

## 数据描述

论文在 MONROE 平台采集 QUIC 客户端与控制服务器的数据交换，因 QUIC 难以直接提取信息而先保存为 qlog，再聚合为 3951 行、188 列的 MonroeQL 表。特征包括 RTT、拥塞窗口、会话时长和吞吐的均值、分位数、最小值、最大值及不同时间/数据量步长统计。

## 公开性核验

作者官方仓库 `GCGImdea/NetPredict-Public` 当前提交 `6dd004fcdc3e460656460db7324fc6bfeb54f964` 公开 XMLAD 笔记本、合成数据、决策树和图件，但没有 MonroeQL 原始 qlog，也没有论文所述 3951×188 数据表。README 只说明代码的 GPLv3 许可，没有给出数据下载链接。

## 对 R2 的裁决

即使取得聚合表，它也缺包号空间、ACK 关系和逐包端点丢失事件，最多是 B 级性能统计。按当前公开制品则判为 C，不能作为可复现实验依赖。

论文中的“异常”是网络性能异常，由无监督方法依据会话时长等指标构造，不是恶意流量标签。

## 文献信息

- DOI：<https://doi.org/10.1016/j.comcom.2023.01.003>
- 官方代码：<https://github.com/GCGImdea/NetPredict-Public>

