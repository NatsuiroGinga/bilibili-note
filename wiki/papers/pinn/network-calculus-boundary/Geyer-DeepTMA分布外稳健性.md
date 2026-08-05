---
title: "DeepTMA 竞争模型预测的分布外稳健性"
authors: [Fabien Geyer, Steffen Bondorf]
year: 2019
date: 2026-07-30
journal: "arXiv 1911.10522"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2019-Geyer-Robustness-DeepTMA.pdf]]"
key_finding: "训练于小网络的竞争模型选择器可外推到更大合成网络，但结论仍局限于同一网络演算建模域，输出多个候选只能降低选择误差，不能修复错误物理模型。"
tags: [网络演算, 分布外泛化, 图神经网络, 类型/论文]
aliases: [Geyer2019Robustness, DeepTMA Robustness]
---

# DeepTMA 竞争模型预测的分布外稳健性

## 一句话

论文验证学习型网络演算组件的规模外推，但没有验证从互联网被动流量迁移到未知拓扑和未知服务过程。

## 方法与证据

- PDF 第 1 至 2 页报告在训练网络小两个数量级时，大网络上的平均相对误差仍低于 1%。
- 输出多个竞争模型候选可使误差约降低一半。
- 训练、验证和测试都来自已知服务器、流、路径、到达曲线和服务曲线的同一合成建模域。

## 本课题裁决

R3 的跨数据集验证不能引用该结果作为直接支持。若实验使用 ns-3 训练、公共数据测试，必须另做信息缺失门控和边界覆盖审计；Top-K 候选不是解决不可辨识性的办法。

## 文献信息

- arXiv: https://arxiv.org/abs/1911.10522
- Zotero: `AWS69JCC`
