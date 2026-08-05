---
title: "带宽估计的最小加系统论方法"
authors: [Jörg Liebeherr, Markus Fidler, Shahrokh Valaee]
year: 2008
date: 2026-07-30
journal: "arXiv 0801.0455；后发表于 IEEE/ACM Transactions on Networking"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2008-Liebeherr-System-Theoretic-Bandwidth-Estimation.pdf]]"
key_finding: "服务曲线可由主动包列或满足条件的被动到达/离开样本估计，但真实 FIFO 网络并非普遍最小加线性，最有信息的观测位于线性到非线性转换处。"
tags: [PINN, 网络演算, 服务曲线反演, 类型/论文]
aliases: [Liebeherr2008, System Theoretic Bandwidth Estimation]
---

# 带宽估计的最小加系统论方法

## 一句话

论文把可用带宽估计解释为服务曲线反演，明确了 R3 若要学习服务下界，至少需要主动探测或同一系统的累计到达与离开观测。

## 方法与证据

- PDF 第 1 页给出从探测包序列或被动样本路径估计服务曲线的任务。
- PDF 第 2 页指出单个 FIFO 链路也不满足普遍的最小加线性，只能区分低负载线性区与过载非线性区。
- 方法依赖常速包列、响应曲线和已定义观测点；部分既有方法还假定链路容量已知。

## 本课题裁决

普通分类 CSV 只有聚合窗口统计，不等价于该论文的系统输入/输出轨迹。R3 只能在 ns-3 主动构造率扫描或累计到达－离开对；若公共数据没有对应观测，推理时必须关闭服务界分支或仅使用到达包络。

## 文献信息

- arXiv: https://arxiv.org/abs/0801.0455
- Zotero: `RRK3HVZG`
