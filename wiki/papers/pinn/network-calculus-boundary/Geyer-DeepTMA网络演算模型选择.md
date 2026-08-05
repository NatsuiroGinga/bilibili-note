---
title: "DeepTMA：用图网络选择网络演算竞争模型"
authors: [Fabien Geyer, Steffen Bondorf]
year: 2019
date: 2026-07-30
journal: "IEEE INFOCOM 2019"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2019-Geyer-DeepTMA.pdf]]"
key_finding: "学习器只选择已证明有效的网络演算分解，最终边界仍由解析规则计算；这说明学习组件不能自行赋予未知服务状态以保证语义。"
tags: [网络演算, 图神经网络, 模型选择, 类型/论文]
aliases: [Geyer2019, DeepTMA]
---

# DeepTMA：用图网络选择网络演算竞争模型

## 一句话

DeepTMA 用图网络替代昂贵的组合搜索，但保留网络演算对最终边界的控制，因此机器学习只影响紧致度和速度，不改变有效性。

## 方法与证据

- PDF 第 1 页报告相对最优 TMA 的最大相对误差低于 6%，运行时间近似稳定。
- PDF 第 5 页的数据由 10 万个合成网络、200 多万条流和近 6000 万个分解样本构成，包含拓扑、路径、到达与服务参数。
- 其输入信息远多于 GeNIS/TQH 的共享统计视图。

## 本课题裁决

R3 可借鉴“学习器只在合法候选中选择”的原则：服务下界头应受单调、非负、保守覆盖等约束。若服务参数本身来自无真值预测，不能援引 DeepTMA 声称解析保证仍成立。

## 文献信息

- DOI: https://doi.org/10.1109/INFOCOM.2019.8737496
- Zotero: `IM4PBA7B`
