---
title: "PRED 数据中心队列显式建模与稳定控制"
authors:
  [
    Xinle Du,
    Tong Li,
    Guangmeng Zhou,
    Zhuotao Liu,
    Hanlin Huang,
    Xiangyu Gao,
    Mowei Wang,
    Kun Tan,
    Ke Xu,
  ]
year: 2025
date: 2026-07-24
journal: "USENIX NSDI 2025"
source_pdf: "[[raw/papers/pinn/pcap/2025-Du-PRED-DCTCP流体模型.pdf]]"
key_finding: "显式建模流并发度、队列与 RED 参数能在现代数据中心稳定控制排队性能，但证据限定于 DCTCP/ECN 和可编程交换机环境。"
tags:
  - PINN
  - 数据中心网络
  - 拥塞控制
  - 类型/论文
aliases:
  - PRED
  - Du2025-PRED
related:
  - "[[Misra-TCP-AQM流体模型]]"
---

# PRED 数据中心队列显式建模与稳定控制

> Xinle Du 等，2025，USENIX NSDI · 21 页

## 一句话

PRED 用流并发稳定器和队列长度调节器动态选择 RED 参数，在真实测试床和大规模仿真中降低队列与尾部流完成时间。

## 背景：问题的演进

固定 RED 阈值难以适应流并发和负载变化，直接用强化学习调参又可能产生不稳定队列波动。

## 方法核心

- 显式建模流并发与稳态队列之间的关系。
- 用渐进测试和验证调节队列目标。
- 在可编程交换机数据平面实现原型。

## 实验结果

论文报告相对静态阈值队列长度降低约 66%，流完成时间最高降低约 80%；相对学习型方法尾部流完成时间降低约 34%。

## 我的理解

这篇现代系统论文说明队列动力学并未过时，但它不证明旁路 PCAP 能恢复这些状态，也不证明相同模型适用于互联网 C2 流量。

## 与相关工作的关系

延续 TCP/AQM 显式建模思想，并以工程系统结果说明模型驱动控制的稳定性价值。

## 疑问 / 待验证

其 DCTCP/ECN 状态和数据中心短流假设不能直接迁移到 TQH-C2 的 TLS、QUIC 和应用层加密流量。

## 原始摘要

原文见 PDF 第 2 页；本笔记不重复长段原文。

## 文献信息

- USENIX: https://www.usenix.org/conference/nsdi25/presentation/du
