---
title: "基于自适应到达约束曲线的隐藏异常检测"
authors: [Anne Bouillard, Aurore Junier, Benoit Ronot]
year: 2012
date: 2026-07-30
journal: "8th International Conference on Network and Service Management"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2012-Bouillard-Hidden-Anomaly-Network-Calculus.pdf]]"
key_finding: "多层时间窗口的自适应到达约束能在线暴露消息流斜率突变，无需恢复服务曲线，因此是 R3 在服务不可辨识时最有依据的降级路线。"
tags: [网络演算, 异常检测, 到达包络, 类型/论文]
aliases: [Bouillard2012, Hidden Anomaly Detection]
---

# 基于自适应到达约束曲线的隐藏异常检测

## 一句话

论文只建模消息到达序列，通过多个时间尺度的约束曲线检测 OSPF 流斜率变化，没有伪造不可观测的服务曲线。

## 方法与证据

- PDF 第 1 页定义连续时间窗口对流量的上下约束，并在违反后更新约束。
- 第 4 至 8 页在 17 节点虚拟 OSPF 网络上分析正常、恶意周期性故障和收敛扰动。
- 方法面向具有稳定协议周期的消息流，不代表任意互联网加密流量都服从相同约束。

## 本课题裁决

若 R3 的服务头无法通过可辨识门槛，应降级为“多尺度条件到达包络 + 校准越界风险”。这一路线仍可检测突发异常，但不能声称积压、时延或端到端服务保证。

## 文献信息

- 作者原件: https://www.di.ens.fr/~bouillard/Publis/CNSM12.pdf
- Zotero: `4DMN77VE`
