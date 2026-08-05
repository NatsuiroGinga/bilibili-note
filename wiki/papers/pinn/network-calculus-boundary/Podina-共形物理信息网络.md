---
title: "共形化物理信息神经网络"
authors: [Lena Podina, Mahdi Torabi Rad, Mohammad Kohandel]
year: 2024
date: 2026-07-30
journal: "ICLR 2024 AI4Differential Equations in Science Workshop"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2024-Podina-Conformalized-PINN.pdf]]"
key_finding: "拆分共形可为 PINN 解和反演参数提供有限样本边际覆盖，但需要独立校准样本与交换性，且逆问题实验为每个数据集单独训练 PINN。"
tags: [PINN, 共形预测, 不确定性量化, 类型/论文]
aliases: [Podina2024, Conformalized PINN]
---

# 共形化物理信息神经网络

## 一句话

论文证明 PINN 可以后处理成覆盖区间，但这不是把共形分数直接加入训练损失，也没有处理跨数据集分布漂移。

## 方法与证据

- PDF 第 1 至 3 页以独立校准集的绝对误差分位数扩展点预测区间。
- PDF 第 4 页的逆问题需要为每个新数据集重新初始化并训练一个 PINN。
- 有效性来自校准与测试交换性；模型拟合差时区间可保持覆盖，但会变宽。

## 本课题裁决

R3 可用共形分位数校准状态或服务下界的覆盖，但必须冻结模型后校准。共形模块不应被写成带来检测精度的必然原因，区间宽度和拒识率必须同时报告。

## 文献信息

- arXiv: https://arxiv.org/abs/2405.08111
- Zotero: `FVYWHANW`
