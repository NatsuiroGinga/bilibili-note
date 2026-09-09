---
title: "Online Continual Learning with Maximally Interfered Retrieval"
authors: [Rahaf Aljundi, Lucas Caccia, Eugene Belilovsky, Massimo Caccia, Min Lin, Laurent Charlin, Tinne Tuytelaars]
year: 2019
date: 2026-09-09
journal: "NeurIPS 2019；arXiv:1908.04742v3"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2019-Aljundi-MIR-Maximally-Interfered-Retrieval.pdf]]"
tags:
  - 持续学习
  - 干扰检索
  - 回放
  - 类型/论文
key_finding: "MIR 用虚拟更新估计哪些记忆样本会受到当前样本最大干扰，再优先取出这些样本回放；它改变的是回放取样，不是 reservoir 入库规则。"
method: "Experience-MIR、Generative-MIR、虚拟参数更新后的损失增量"
baseline: "随机回放、ER、生成式回放"
aliases: [MIR, Maximally Interfered Retrieval]
---

# MIR：最大干扰检索

## 方法核心

- §3.1、算法 1 在 reservoir 中先估计当前数据对候选记忆的虚拟损失变化，再选择预测会被最严重损害的样本。
- 该方法的关键是“取出哪些样本”，不是“新样本到达后如何入库”；若每年把全部 200 条记忆拼接进训练集，top-200 检索不会产生独立选择效应。
- §3.1 的干扰分数可写为 `s(x)=loss(f_{theta^v}(x))-loss(f_theta(x))`，其中 `theta^v` 是当前批次造成的虚拟更新参数；原 ER-MIR 的 reservoir 写入仍独立存在。

## 对 LAMDA 的关系

- 可作为“保护角色／干扰信号”的强对照，或仅用于下一轮记忆保留。
- 若改变为 batch 级动态检索，必须固定与随机检索相同的抽取次数、样本暴露量和额外计算预算。

## 不能直接声称

- MIR 的视觉基准收益不证明它能降低 LAMDA 的 FPR 或恶意负向翻转。
- MIR 不能替代双侧风险约束；它只提供干扰排序。
- CIFAR-10 每类记忆 100 的表 2 中，ER 与 ER-MIR 准确率分别为 `41.3±1.9%` 与 `47.6±1.1%`；这是视觉基准结果。

## 一句话

MIR 用虚拟更新估计旧记忆中最可能被当前数据伤害的样本，并优先检索这些样本回放。

## 背景：问题的演进

随机回放不区分当前更新对不同旧样本的干扰程度；MIR 将取样重点转向预计损失增量最大的记忆。

## 我的理解

MIR 解决的是“这一步取哪些旧样本”，不是“新样本如何进入记忆”。在本课题每年把全部 200 条记忆拼入训练的实现中，单纯 top-200 检索没有独立作用。

## 与相关工作的关系

MIR 与 GSS、ECBRS/PAPA 共同构成回放选择和干扰估计的强对照；它不能替代双侧风险约束。

## 疑问 / 待验证

- 若改成 batch 级动态检索，如何固定随机检索的抽取次数和样本暴露量？
- 虚拟更新的额外开销是否会改变 LAMDA 单卡公平性？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- arXiv：https://arxiv.org/abs/1908.04742
- HTML：https://arxiv.org/html/1908.04742v3
