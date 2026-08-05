---
title: "结构预测中的可微动态规划"
authors: [Arthur Mensch, Mathieu Blondel]
year: 2018
date: 2026-07-30
journal: "ICML 2018"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2018-Mensch-Differentiable-Dynamic-Programming.pdf]]"
key_finding: "强凸正则化的平滑最大算子能把一类动态规划变成可微层，并给出原最大值与平滑值之间的显式上下界。"
tags: [可微优化, 动态规划, 误差界, 类型/论文]
aliases: [Mensch2018, Differentiable Dynamic Programming]
---

# 结构预测中的可微动态规划

## 一句话

论文给出比 Soft-DTW 更一般的平滑动态规划框架，适合支撑 R3 对上确界和最小加递推的可微化及误差控制。

## 方法与证据

- PDF 第 1 页用强凸正则化平滑最大算子，使最优值和解都可反向传播。
- PDF 第 2 页引理 1 给出硬最大值与平滑最大值的上下界，误差由正则化函数在概率单纯形上的范围控制。
- 负熵得到稠密软路径，平方二范数可产生稀疏期望路径。

## 本课题裁决

R3 应使用有限窗口递推，并报告近似误差上界、温度、候选数和梯度范数。平滑运算只解决“能否训练”，不解决输入服务曲线是否真实。

## 文献信息

- arXiv: https://arxiv.org/abs/1802.03676
- Zotero: `WXCSQ6M4`
