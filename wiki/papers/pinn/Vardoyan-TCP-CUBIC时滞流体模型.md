---
title: "TCP Reno 与 CUBIC 的时滞流体模型"
authors: [Gayane Vardoyan, C. V. Hollot, Don Towsley]
year: 2018
date: 2026-07-24
journal: "arXiv:1801.02741"
source_pdf: "[[raw/papers/pinn/pcap/2018-Vardoyan-TCP-CUBIC流体模型.pdf]]"
key_finding: "以最大拥塞窗口、距最近丢包时间、反馈时延和丢包概率构成的时滞方程可统一描述 Reno 与 CUBIC，但高度依赖传输协议内部状态。"
tags:
  - PINN
  - TCP
  - 时滞系统
  - 类型/论文
aliases:
  - Vardoyan2018
  - TCP CUBIC 流体模型
related:
  - "[[Misra-TCP-AQM流体模型]]"
---

# TCP Reno 与 CUBIC 的时滞流体模型

> Gayane Vardoyan、C. V. Hollot、Don Towsley，2018，arXiv · 28 页

## 一句话

论文用时滞泛函微分方程表示最近丢包后的窗口演化，验证框架与经典 Reno 模型等价，并推导 CUBIC 的局部稳定性。

## 背景：问题的演进

经典流体模型适合 Reno 的加性增长，却难以表达 CUBIC 由最大窗口和距最近丢包时间决定的非线性窗口轨迹。

## 方法核心

- 状态包含最近丢包前最大窗口和距最近丢包时间。
- 丢包反馈以一个往返时延后的概率项进入方程。
- 用不同窗口函数实例化 Reno 与 CUBIC。

## 实验结果

论文用仿真验证流体模型，并从理论上证明所研究 CUBIC 平衡点的局部一致渐近稳定性。

## 我的理解

这是协议专用 PINN 的强理论来源，但不是通用恶意流量方程。旁路 PCAP 缺少端点拥塞窗口，QUIC 的确认信息又通常不可见，因此应只在 ns-3 或 TCP 可观测子集做条件验证。

## 与相关工作的关系

扩展 Misra 等 TCP/AQM 流体思想；二维 TCP/AQM 模型进一步强调顺序事件和双时间尺度。

## 疑问 / 待验证

若 ns-3 使用不同拥塞控制算法，模型参数与状态定义必须重新核验，不能靠统一标签掩盖差异。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- arXiv: https://arxiv.org/abs/1801.02741
