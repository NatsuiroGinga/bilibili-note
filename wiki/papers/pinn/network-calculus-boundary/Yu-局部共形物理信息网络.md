---
title: "物理信息神经网络的局部共形不确定性框架"
authors: [Yifan Yu, Cheuk Hin Ho, Yangshuai Wang]
year: 2025
date: 2026-07-30
journal: "arXiv 2509.13717"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2025-Yu-Conformal-PINN.pdf]]"
key_finding: "局部共形分位数能适应空间异方差并保持有限样本覆盖，但论文尚未处理部分观测逆问题、时间依赖或跨域流量漂移。"
tags: [PINN, 共形预测, 局部校准, 类型/论文]
aliases: [Yu2025, Local Conformal PINN]
---

# 物理信息神经网络的局部共形不确定性框架

## 一句话

论文把启发式不确定性分数校准为覆盖区间，并按局部状态调整区间宽度，为 R3 的“协议/状态条件化置信门控”提供方法参考。

## 方法与证据

- PDF 第 1 至 2 页说明全局共形区间在异方差区域可能过宽或欠覆盖。
- PDF 第 8 页要求独立于训练集的有标签校准集。
- 第 5 节的局部分位数方法保持总体有限样本覆盖；第 6 节把逆问题、部分观测和时间依赖列为未来工作。

## 本课题裁决

R3 不能声称该方法已经解决网络流量时序漂移。可采用按协议族、可见性掩码和负载区间分组的校准分数，但每组必须有最低样本量，并同时报告总体与最差组覆盖。

## 文献信息

- arXiv: https://arxiv.org/abs/2509.13717
- Zotero: `4AA6NXB6`
