---
title: "RouteNet-Erlang 复杂网络性能建模"
authors:
  [
    Miquel Ferriol-Galmés,
    Krzysztof Rusek,
    José Suárez-Varela,
    Shihan Xiao,
    Xiang Shi,
    Xiangle Cheng,
    Bo Wu,
    Pere Barlet-Ros,
    Albert Cabellos-Aparicio,
  ]
year: 2022
date: 2026-07-24
journal: "arXiv:2202.13956"
source_pdf: "[[raw/papers/pinn/pcap/2022-Ferriol-RouteNet-Erlang.pdf]]"
key_finding: "图神经网络可在复杂业务模型、多队列调度和未见拓扑上优于经典排队模型，但依赖容量、队列和业务描述特征。"
tags:
  - PINN
  - 图神经网络
  - 网络性能
  - 类型/论文
aliases:
  - RouteNet-Erlang
  - Ferriol2022
related:
  - "[[Helm-网络演算辅助时延预测]]"
---

# RouteNet-Erlang 复杂网络性能建模

> Miquel Ferriol-Galmés 等，2022，arXiv · 10 页

## 一句话

RouteNet-Erlang 将流、队列和链路建成消息传递图，以容量、缓冲、调度和业务模型参数预测时延、抖动与丢失。

## 背景：问题的演进

经典排队论常要求泊松或特定到达分布，难以覆盖真实复杂业务；逐包仿真准确但计算成本高。

## 方法核心

- 为流、队列和链路分别维护隐状态。
- 沿路径和队列关系反复消息传递。
- 用容量相对尺度和业务模型参数提高跨规模泛化。

## 实验结果

论文报告在多种业务、队列调度和路由条件下优于所选排队论基线，并能泛化到训练未见网络。

## 我的理解

这是一种数据驱动网络数字孪生，不是 PINN。它适合作为“复杂业务统计不能被简单队列假设覆盖”的证据，也说明公平比较需要给模型相同的拓扑和容量输入。

## 与相关工作的关系

Helm 与 Zhang 在类似图模型中加入网络演算上界，形成形式化理论与数据驱动模型结合的路线。

## 疑问 / 待验证

本项目的公开恶意流量数据缺少完整拓扑和队列描述，无法直接复现 RouteNet-Erlang 的输入条件。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- arXiv: https://arxiv.org/abs/2202.13956
