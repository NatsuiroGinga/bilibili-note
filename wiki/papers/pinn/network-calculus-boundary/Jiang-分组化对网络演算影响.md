---
title: "分组化对网络演算分析的影响"
authors: [Yuming Jiang]
year: 2025
date: 2026-07-30
journal: "arXiv 2509.17028"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2025-Jiang-Packetization-Impact.pdf]]"
key_finding: "忽略分组化不仅会破坏服务曲线，还可连带破坏输出界、积压界和串联系统界，因此连续流近似必须显式声明适用条件。"
tags: [网络演算, 分组化, 积压边界, 类型/论文]
aliases: [Jiang2025Packetization, Packetization Impact]
---

# 分组化对网络演算分析的影响

## 一句话

论文用更系统的反例说明错误服务曲线会沿推导链污染多个边界，不能靠最终实验拟合较好来挽救理论错误。

## 方法与证据

- PDF 第 1 页列出服务、输出、积压和串联界的反例范围。
- PDF 第 7 至 8 页给出分组系统中的反例与修正服务表达。
- PDF 第 13 页总结必须在服务模型中直接计入分组化。

## 本课题裁决

R3 不采用纯连续比特流的确定性最坏界。可行实现应在有限窗口内使用实际包长累计，并把平滑边界解释为训练正则和经验覆盖对象，而不是未经验证的严格最坏保证。

## 文献信息

- arXiv: https://arxiv.org/abs/2509.17028
- Zotero: `WM6IACHM`
