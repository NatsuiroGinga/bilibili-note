---
title: "QUIC 隐蔽信道流量数据集"
authors: [Aleksandar Velinov, Aleksandra Mileva, Simon Volpert, Sebastian Zillien, Steffen Wendzel]
year: 2026
date: 2026-08-03
journal: "Journal of Universal Computer Science 32(2)"
source_pdf: "[[raw/papers/datasets/quic/Steganography-in-the-QUIC-Communication-Protocol-2026.pdf]]"
tags:
  - QUIC
  - 隐蔽信道
  - 加密流量
  - 数据集
  - 类型/论文
aliases:
  - QUIC Dataset 2025
  - Velinov2026-Steganography
key_finding: "数据用 QUIC Retry Token 承载 ASCII 或 AES 隐蔽信息，提供 16 个 CSV、实际总计 878.3 MB；它有窄域异常标签但没有端点动力学状态。"
---

# QUIC 隐蔽信道流量数据集

## 一句话

这是一个有安全语义的 QUIC 数据集，但标签只覆盖 Retry Token 隐蔽信道，无法替代通用攻击数据或完整动力学教师。

## 数据与实验

论文系统分析 QUIC 中 20 种潜在隐蔽信道，并实现以 Retry Token 承载消息的原型。公开数据由 6 个 ASCII 隐蔽信道 CSV、6 个 AES 隐蔽信道 CSV 和 4 个正常流量 CSV 构成，Zenodo 实际文件合计 878.3 MB。

Zenodo 页面显示的 31.1 GB 是累计下载数据量，不是数据集文件大小。论文与数据文件没有表明提供 PCAP、qlog、ACK、端点丢包、RTT、在途字节或拥塞窗口。

## 对 R2 的作用

可作为“协议专属安全特征是否产生增益”的窄域外部诊断，尤其检查 Retry Token 特征是否会让模型只记住攻击实现。它不应进入完整 QUIC 动力学残差主训练，也不能用于声称对多类 QUIC 攻击泛化。

## 不可声称

- AES 类表示隐蔽载荷编码方式，不等于一般加密恶意流量。
- Retry Token 统计差异不等于拥塞或恢复动力学。
- 三类场景不能代表 H23Q 的十类攻击范围。

## 文献信息

- DOI：<https://doi.org/10.3897/jucs.154672>
- 数据 DOI：<https://doi.org/10.5281/zenodo.15076824>

