---
title: "面向时间敏感网络的网络演算边界重审"
authors: [Yuming Jiang]
year: 2024
date: 2026-07-30
journal: "arXiv 2403.13656"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2024-Jiang-Network-Calculus-Revisit.pdf]]"
key_finding: "忽略分组化会使常用最小加服务模型和时延界失效；对分组网络应结合最大加服务语义或显式分组修正。"
tags: [网络演算, 分组化, 反例, 类型/论文]
aliases: [Jiang2024, Network Calculus Revisit]
---

# 面向时间敏感网络的网络演算边界重审

## 一句话

论文用反例说明面向比特流的连续服务曲线不能不加修正地用于分组网络，这是 R3 公式设计的硬性边界。

## 方法与证据

- PDF 第 1 至 2 页指出多个基本最小加服务模型忽略分组最后一比特到达语义，相关时延界因此可失效。
- 论文提出最大加 `g` 服务模型及其扩展，并与最小加到达曲线组合。
- 结论针对时间敏感网络中的明确链路和调度设置，不能直接给互联网流量的通用服务曲线。

## 本课题裁决

R3 的累计量必须同时保留字节数和最大包长或包长分位数，并加入至少一个包级修正消融。若共享视图无法提供包长，完整网络演算候选必须否决。

## 文献信息

- arXiv: https://arxiv.org/abs/2403.13656
- Zotero: `AEFIQD7G`
