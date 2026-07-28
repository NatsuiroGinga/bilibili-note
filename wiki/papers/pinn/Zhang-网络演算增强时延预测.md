---
title: "网络演算增强的图神经网络时延预测"
authors: [Lianming Zhang, Benle Yin, Qian Wang, Pingping Dong]
year: 2023
date: 2026-07-24
journal: "IFIP Networking 2023"
source_pdf: "[[raw/papers/pinn/pcap/2023-Zhang-网络演算增强时延预测.pdf]]"
key_finding: "漏桶到达曲线、速率－时延服务曲线和多节点卷积可给出端到端时延上界，但 NetCTRT 仍将该上界作为图神经网络输入。"
tags:
  - PINN
  - 网络演算
  - 图神经网络
  - 类型/论文
aliases:
  - Zhang2023-NetCTRT
  - NetCTRT
related:
  - "[[Helm-网络演算辅助时延预测]]"
---

# 网络演算增强的图神经网络时延预测

> Lianming Zhang、Benle Yin、Qian Wang、Pingping Dong，2023，IFIP Networking · 7 页

## 一句话

NetCTRT 用到达曲线约束流量速率和突发量，用服务曲线描述节点最低服务，并把端到端时延上界加入图神经网络输入。

## 背景：问题的演进

网络演算解释性强但依赖简化假设，图神经网络能拟合复杂网络却难以解释内部关系。

## 方法核心

- 用最小加卷积描述到达与服务。
- 用漏桶模型参数化到达曲线。
- 用速率－时延模型和多节点服务曲线卷积计算时延上界。
- 将拓扑、路由、流量和上界共同输入 RouteNet 派生模型。

## 实验结果

论文报告 NetCTRT 比原始 RouteNet 和 PLNet 获得更低的端到端时延预测误差。

## 我的理解

这篇论文给网络演算备选提供了完整变量和边界来源，但其组合方式仍是特征增强。公开 PCAP 只能估计到达包络，服务曲线必须来自 ns-3、设备配置或测试床。

## 与相关工作的关系

Helm 与 Carle 在硬件测试床上验证网络演算特征对高分位时延预测的作用。

## 疑问 / 待验证

最坏时延界可能过松，低违反率不必然意味着状态预测准确，需要同时报告绝对状态误差。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- DOI: https://doi.org/10.23919/IFIPNETWORKING57963.2023.10186434
