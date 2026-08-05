---
title: "多步时间序列的共形预测"
authors: [Kamilė Stankevičiūtė, Ahmed M. Alaa, Mihaela van der Schaar]
year: 2021
date: 2026-07-30
journal: "NeurIPS 2021"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2021-Stankeviciute-Conformal-Time-Series.pdf]]"
key_finding: "共形时间序列方法把整条独立序列视作交换单位；直接把单条流内相邻窗口当作交换样本在方法上无效。"
tags: [共形预测, 时间序列, 覆盖率, 类型/论文]
aliases: [Stankeviciute2021, Conformal Time-Series Forecasting]
---

# 多步时间序列的共形预测

## 一句话

论文为多步预测构造覆盖区间，但其关键设计是把多条独立时间序列作为交换样本，而不是忽略单条序列内部依赖。

## 方法与证据

- PDF 第 1 页给出多预测步的频率覆盖目标。
- PDF 第 3 页明确说明单条序列内部时间点不交换，朴素共形校准没有有效性保证。
- 方法假设数据包含多条独立序列，并把每条完整序列作为一个观测单位；多变量扩展留作未来工作。

## 本课题裁决

R3 的拆分单位必须是完整流、会话或独立仿真运行，不能随机打散相邻四窗口。公共数据按流分组校准；同一流的窗口只能保持时序整体进入一个分区。

## 文献信息

- 官方页面: https://proceedings.neurips.cc/paper/2021/hash/312f1ba2a72318edaaa995a67835fad5-Abstract.html
- Zotero: `7DKD3WQH`
