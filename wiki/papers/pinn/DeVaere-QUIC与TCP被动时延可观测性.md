---
title: "QUIC 与 TCP 的被动时延可观测性"
authors: [Piet De Vaere, Tobias Bühler, Mirja Kühlewind, Brian Trammell]
year: 2018
date: 2026-07-24
journal: "Internet Measurement Conference 2018"
source_pdf: "[[raw/papers/pinn/pcap/2018-DeVaere-QUIC-TCP被动时延测量.pdf]]"
key_finding: "QUIC 加密确认与控制信息使普通旁路观察者无法像 TCP 那样关联双向包，显式旋转信号才恢复有限的往返时延观测。"
tags:
  - PINN
  - QUIC
  - 被动测量
  - 类型/论文
aliases:
  - DeVaere2018
  - Three Bits Suffice
related:
  - "[[Habib-输出链路轨迹队列反演]]"
---

# QUIC 与 TCP 的被动时延可观测性

> Piet De Vaere 等，2018，Internet Measurement Conference · 7 页

## 一句话

QUIC 将确认等传输控制信息隐藏在加密部分，论文通过一个旋转位和两位有效边缘计数器，让旁路观察者在不解密载荷的情况下估计往返时延。

## 背景：问题的演进

TCP 时间戳和序列确认关系支持被动往返时延测量，而 QUIC 的加密设计主动减少网络中可见的传输内部状态。

## 方法核心

- 每包公开一个旋转位，端点按往返反馈切换。
- 额外两位标识旋转边缘是否受应用延迟等因素污染。
- 在仿真和互联网测试床上检验丢包与乱序下的测量可用性。

## 实验结果

论文报告显式信号能以较小端点状态和协议开销支持单点被动往返时延测量，并对较强丢包和乱序保持可用。

## 我的理解

该结果为统一 TCP/QUIC 物理状态设置了否决边界。若 TQH-C2 QUIC 报文没有可用旋转位或端点日志，就不能把确认关系、拥塞窗口或精确往返时延当作可观测输入。

## 与相关工作的关系

与 TCP/AQM 流体模型形成观测条件互补：后者给出动力学状态，本文说明哪些状态对旁路 PCAP 实际不可见。

## 疑问 / 待验证

TQH-C2 的 QUIC 实现是否启用旋转位，以及抓包点是否足以稳定读取，需要直接检查 PCAP。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- DOI: https://doi.org/10.1145/3278532.3278535
