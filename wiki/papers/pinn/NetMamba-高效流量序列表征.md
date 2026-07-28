---
title: "NetMamba 高效流量序列表征"
authors:
  [Tongze Wang, Xiaohui Xie, Wenduo Wang, Chuyi Wang, Youjian Zhao, Yong Cui]
year: 2024
date: 2026-07-24
journal: "arXiv:2405.11449"
source_pdf: "[[raw/papers/pinn/pcap/2024-Wang-NetMamba流量表征.pdf]]"
key_finding: "单向状态空间模型能以线性序列复杂度处理去偏后的原始流量表示，适合作为 PCAP 编码效率参考，但不提供物理方程。"
tags:
  - PINN
  - Mamba
  - 加密流量
  - 类型/论文
aliases:
  - NetMamba
  - Wang2024-NetMamba
related:
  - "[[YaTC-多层流量表征]]"
---

# NetMamba 高效流量序列表征

> Tongze Wang 等，2024，arXiv · 11 页

## 一句话

NetMamba 为网络流量设计线性复杂度状态空间编码器和去偏表示，在多个分类任务上兼顾精度、速度和少样本能力。

## 背景：问题的演进

Transformer 自注意力对长包序列具有平方复杂度，现有原始流量表示还可能丢失有效字节或保留地址端口偏差。

## 方法核心

- 使用针对网络流量调整的单向 Mamba。
- 对原始流量做有效信息保留和偏差消除。
- 以无标签预训练后微调下游分类任务。

## 实验结果

论文在六个公开数据集上报告超过 90% 的多项准确率，并给出最高约 60 倍的推理加速结果。

## 我的理解

若 PCAP 序列长度成为 5090 上的瓶颈，可借鉴轻量状态空间编码器。但当前最小探针应先验证字段可辨识性，不应同时更换 Qwen 主干或引入大规模预训练。

## 与相关工作的关系

与 ET-BERT、YaTC 同属加密流量表征，不属于 PINN 理论来源。

## 疑问 / 待验证

预印本结果和数据去偏细节需要在正式采用为外部基线前再次核验公开实现。

## 原始摘要

原文见 PDF 第 1 页；本笔记不重复长段原文。

## 文献信息

- arXiv: https://arxiv.org/abs/2405.11449
