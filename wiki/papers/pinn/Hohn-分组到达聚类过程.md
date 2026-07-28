---
title: "分组到达的聚类点过程模型"
authors: [Nicolas Hohn, Darryl Veitch, Patrice Abry]
year: 2003
date: 2026-07-24
journal: "IEEE Transactions on Signal Processing"
source_pdf: "[[raw/papers/pinn/pcap/2003-Hohn-分组到达聚类过程.pdf]]"
key_finding: "聚类点过程能用流到达、流内包结构和包数重尾解释分组流量的多尺度统计，但它仍是统计模型而非控制方程。"
tags:
  - PINN
  - 点过程
  - 流量突发
  - 类型/论文
aliases:
  - Hohn2003
  - Cluster Processes
related:
  - "[[Paxson-广域流量非泊松性]]"
---

# 分组到达的聚类点过程模型

> Nicolas Hohn、Darryl Veitch、Patrice Abry，2003，IEEE Transactions on Signal Processing · 11 页

## 一句话

将每条流视为一个包到达簇，可以用具有网络语义的参数解释小尺度流内结构和大尺度长程相关。

## 背景：问题的演进

自相似和多重分形模型能拟合统计曲线，却难以说明参数与流、包和网络机制的关系。论文提出半经验的聚类点过程替代黑盒统计描述。

## 方法核心

- 用流到达过程生成簇中心。
- 用流持续时间、包数量和流内到达结构生成包簇。
- 通过小波谱、到达间隔分布和仿真比较模型与真实轨迹。

## 实验结果

论文把小尺度结构归因于流内包模式，把长程相关主要归因于每流包数的重尾，并指出会话级建模对包级统计并不充分。

## 我的理解

点过程可用于 PCAP 时序编码器、到达强度估计和负对照，但其似然是统计约束。只有当预测到达强度与服务、占用和守恒状态共同进入可微方程时，才可能成为 PINN 的组成部分。

## 与相关工作的关系

承接 Paxson 与 Floyd 对通用泊松假设的否定，也解释了为何 RouteNet-Erlang 需要支持复杂业务模型。

## 疑问 / 待验证

恶意 C2 的定时行为可能刻意模仿良性流量，聚类参数能否跨采集环境稳定尚不确定。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- DOI: https://doi.org/10.1109/TSP.2003.814460
