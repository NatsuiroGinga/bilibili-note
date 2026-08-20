---
title: "流量分类与检测方法演进论文索引"
date: 2026-08-19
tags:
  - 流量分类
  - 加密恶意流量检测
  - 方法演进
  - 论文索引
  - MOC
  - 类型/MOC
---

# 流量分类与检测方法演进论文索引

本目录收录 `raw/papers/traffic-classification-evolution/` 下的原件笔记，
服务论文第一章 `1.2.1 加密恶意流量检测的表示与判定方法演进`。
本目录只放**演进谱系的时间锚点**，当代方法分别在
`wiki/papers/traffic-foundation-models/`、`wiki/papers/attack-detection/`、
`wiki/papers/datasets/` 下。

## 一、端口与统计流特征时代（2005）

- **[[2005-Moore-Zuev-朴素贝叶斯流量分类|Moore & Zuev 2005]]** — SIGMETRICS'05。
  248 个按流统计判别量 + 朴素贝叶斯；最简形式 `65%`，加核估计与特征约简超 `95%`。
  原件 p.1 自陈当时传统技术精度只有 `50%–70%`。跨期精度掉到 `20.75%/37.65%`（p.9）。
- **[[2005-Karagiannis-BLINC黑箱多层流量分类|BLINC 2005]]** — SIGCOMM'05。
  原件 p.1 明确"在黑箱中分类"的三条约束：无载荷、不信端口、只用流采集器输出；
  判定单元上移到**主机**，社会／功能／应用三层。`80%–90%` 流量达 `95%+` 精度。
  **这是本课题 NetFlow 观测条件的最早规范表述。**

## 二、部署困难与评价方法学的规范批评（2010）

- **[[2010-Sommer-Paxson-机器学习入侵检测的四重困难|Sommer & Paxson 2010]]** — IEEE S&P'10。
  四项结构性困难：离群检测、错误代价高、语义鸿沟、流量多样性（§III.A–D，p.2–4）。
  与 Arp 2022 分工：前者讲任务结构，后者讲实验设计陷阱，不可互相替代。

## 三、向原始字节深度表示过渡（2019–2020）

- **[[2019-Rezaei-Liu-加密流量深度学习综述|Rezaei & Liu 2019]]** — IEEE Communications Magazine 57(5):76-81。
  过渡引文：端口／DPI／经典 ML 因加密化而退化；同时自陈该路线无公认数据集与统一协议（p.2 §II-B），
  且采集点差异直接改变特征分布。
- **[[2020-Lotfollahi-DeepPacket原始字节端到端分类|Deep Packet 2020]]** — Soft Computing 24(3):1999-2012。
  单报文截断／补零到 `1500` 字节向量喂 1D-CNN（p.6）。
  **该输入构造是「主动排除原始字节路线」段的核心证据：本课题 NetFlow 数据无报文字节。**

## 尚未入库（付费墙阻塞，见 `.Codex/docs/RWKV/2026-08-19-第一二章文献建设/`）

- Nguyen & Armitage 2008, IEEE Communications Surveys & Tutorials 10(4):56-76，DOI `10.1109/SURV.2008.080406`。
- Wang 等 2017, IEEE ISI 2017, pp. 43-48，DOI `10.1109/ISI.2017.8004872`。
