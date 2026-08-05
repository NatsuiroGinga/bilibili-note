---
title: "现代神经网络置信度校准与温度缩放"
authors: [Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger]
year: 2017
date: 2026-07-30
journal: "ICML 2017，PMLR 70"
source_pdf: "[[raw/papers/pinn/protocol-adaptive/2017-Guo-Neural-Network-Calibration.pdf]]"
zotero_item_key: "Y8NQEYKT"
zotero_citekey: "guo_calibration_2017"
zotero_attachment_key: "G9KF74NY"
sha256: "df7c93f97204f8a3c2b10f6d5bf5265baac25f00c1ae3b473a3e1dbc102dacb2"
key_finding: "温度缩放以独立验证集拟合单一正温度，在不改变类别预测的前提下改善同分布置信度；原文明确假定训练、验证和测试同分布。"
tags:
  - 置信度校准
  - 温度缩放
  - 协议识别
  - 类型/论文
aliases:
  - Guo2017-Calibration
  - Temperature Scaling
---

# 现代神经网络置信度校准与温度缩放

## 一句话

协议软强度必须由独立协议真值验证集校准，而不能直接使用未校准的最大软最大概率。

## 方法与证据

- PDF 第 3 页、第 2 节：论文以可靠性图和分箱期望校准误差衡量置信度与经验正确率的差距，同时讨论最大校准误差和适当评分规则。
- PDF 第 4 页、第 4 节：所有事后校准方法都需要留出验证集，且实验假定训练、验证、测试来自同一分布。
- PDF 第 5 页、第 4.2 节：温度缩放为所有类别共享一个正标量 `T`，在验证集上最小化负对数似然；它不改变最大对数几率类别，因此不改变分类准确率。
- PDF 第 7 至 8 页：温度缩放在论文图像和文本基准上通常优于更复杂的事后方法，但这是同分布证据。

## 对 R2 的约束

- `P_cal(protocol | x_proto)` 必须只用训练内部的协议真值校准折拟合，测试标签绝不参与。
- 至少报告负对数似然、Brier 分数、期望校准误差、可靠性图和按协议分层校准；不能只给准确率。
- 置信阈值必须在校准折按预注册覆盖率或风险选择，并在留一数据源上原样使用。
- 校准概率只控制物理专家强度并执行 `stopgrad`，不得接收攻击分类损失。

## 文献信息

- 官方页面：https://proceedings.mlr.press/v70/guo17a.html
