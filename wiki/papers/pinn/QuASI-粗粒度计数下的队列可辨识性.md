---
title: "QuASI 粗粒度计数下的队列可辨识性"
authors: [Divya Raghunathan, Maria Apostolaki, Aarti Gupta]
year: 2025
date: 2026-07-24
journal: "USENIX NSDI 2025"
source_pdf: "[[raw/papers/pinn/pcap/2025-Raghunathan-QuASI队列可辨识性.pdf]]"
key_finding: "端口计数能严格限制可能的队列行为，却因缺少包时序、顺序和路由而不能唯一恢复队列轨迹。"
tags:
  - PINN
  - 队列可辨识性
  - 形式化方法
  - 类型/论文
aliases:
  - QuASI
  - Raghunathan2025
related:
  - "[[Habib-输出链路轨迹队列反演]]"
---

# QuASI 粗粒度计数下的队列可辨识性

> Divya Raghunathan、Maria Apostolaki、Aarti Gupta，2025，USENIX NSDI · 17 页

## 一句话

QuASI 不从粗粒度端口计数直接预测唯一队列，而是在所有与计数相容的包轨迹上形式化判断某个队列性质是否可能成立。

## 背景：问题的演进

细粒度队列监控成本高，常见设备只长期保留分钟级输入、输出和丢弃计数。这些计数与队列相关，却缺少决定队列轨迹的包级细节。

## 方法核心

- 把输入、输出、丢弃计数和队列查询表示为相容包轨迹集合。
- 第一层用无假阴性的抽象快速排除不可能情况。
- 第二层用可满足性模理论求解器做精确验证。

## 实验结果

论文报告第一层在一秒内得到比启发式方法最多紧 58% 的队列上界，第二层可求精确值，并在部分任务上比既有形式方法快多个数量级。

## 我的理解

这是本课题可辨识性门槛的关键证据。PCAP 的时序和方向能缩小相容轨迹集合，但没有正确端口、路由与服务边界时仍不能宣称得到真实队列。

## 与相关工作的关系

Habib 与 Molle 说明在更强观测前提下可做输出链路队列反演；两者共同限定公开 PCAP 的能力边界。

## 疑问 / 待验证

TQH-C2 PCAP 的采集位置与 ns-3 控制体能否形成同构观测，是进入 PINN 训练前必须回答的问题。

## 原始摘要

原文见 PDF 第 2 页；本笔记不重复长段原文。

## 文献信息

- USENIX: https://www.usenix.org/conference/nsdi25/presentation/raghunathan
