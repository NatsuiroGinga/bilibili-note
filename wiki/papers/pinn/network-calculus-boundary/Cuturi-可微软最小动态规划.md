---
title: "软动态时间规整中的可微软最小运算"
authors: [Marco Cuturi, Mathieu Blondel]
year: 2017
date: 2026-07-30
journal: "ICML 2017"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2017-Cuturi-Soft-DTW.pdf]]"
key_finding: "用温度化软最小替换动态规划中的硬最小可获得端到端梯度，但会引入温度偏差和二次时间空间开销。"
tags: [可微优化, 软最小, 时间序列, 类型/论文]
aliases: [Cuturi2017, Soft-DTW]
---

# 软动态时间规整中的可微软最小运算

## 一句话

论文证明动态规划里的最小运算可平滑为可微软最小，为 R3 实现有限窗口最小加卷积提供计算机制，但不提供网络演算正确性。

## 方法与证据

- PDF 第 1 至 2 页定义温度参数控制的软最小，并说明温度趋近零时恢复硬最小。
- 前向值和反向梯度均可计算，基础实现时间与空间复杂度为窗口长度乘积。
- 温度大时边界更平滑但偏差更大；温度接近零时梯度重新集中到单一路径。

## 本课题裁决

R3 只采用“有限候选集合上的软最小/软最大”思想，不照搬时间规整损失。论文中需自行证明有限窗口下 `log-sum-exp` 近似误差，并用温度消融验证梯度与偏差的折中。

## 文献信息

- arXiv: https://arxiv.org/abs/1703.01541
- Zotero: `J4GEJCZZ`
