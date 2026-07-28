---
title: "二维 TCP/AQM 流体模型"
authors:
  [
    Sadek Belamfedel Alaoui,
    Alejandro J. Rojas,
    Abdelaziz Hmamed,
    El Houssaine Tissir,
  ]
year: 2022
date: 2026-07-24
journal: "arXiv:2211.10833"
source_pdf: "[[raw/papers/pinn/pcap/2022-Alaoui-二维TCP-AQM流体模型.pdf]]"
key_finding: "以路由器队列时间与拥塞窗口时间为两个时间基可更细致表示 TCP/AQM 顺序事件，但状态、时延和稳定性分析复杂度明显增加。"
tags:
  - PINN
  - TCP
  - 主动队列管理
  - 类型/论文
aliases:
  - Alaoui2022
  - 二维 TCP AQM
related:
  - "[[Vardoyan-TCP-CUBIC时滞流体模型]]"
---

# 二维 TCP/AQM 流体模型

> Sadek Belamfedel Alaoui 等，2022，arXiv · 9 页

## 一句话

论文认为单一时间基不能充分表示队列与拥塞窗口的连续顺序事件，因而建立二维非线性时滞模型并分析其局部稳定性。

## 背景：问题的演进

已有 TCP/AQM 流体模型在复杂顺序事件下可能产生近似误差。作者把路由器侧和窗口侧动态分离为两个时间维度。

## 方法核心

- 构造二维 Roesser 型 TCP/AQM 状态模型。
- 通过线性化和 Lyapunov 泛函给出稳定条件。
- 提供两个可复现实例的状态空间矩阵。

## 实验结果

论文用两个网络流量场景验证理论稳定条件，但没有面向恶意流量检测或加密协议评估。

## 我的理解

该模型说明“更复杂公式”会显著增加状态和观测需求。当前项目应先通过 PCAP 可辨识性门槛，不能在观测不足时直接采用二维状态系统。

## 与相关工作的关系

承接 Misra 和 Vardoyan 的 TCP/AQM 流体建模，是高复杂度备选而非最小可执行路线。

## 疑问 / 待验证

公开 PCAP 是否足以区分两个时间基对应的隐状态，目前没有证据支持。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- arXiv: https://arxiv.org/abs/2211.10833
