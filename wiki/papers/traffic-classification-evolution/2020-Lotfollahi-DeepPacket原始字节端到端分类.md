---
title: "Deep Packet: A Novel Approach For Encrypted Traffic Classification Using Deep Learning"
authors: [Mohammad Lotfollahi, Mahdi Jafari Siavoshani, Ramin Shirali Hossein Zade, Mohammdsadegh Saberian]
year: 2020
date: 2026-08-19
journal: "Soft Computing, 24(3):1999-2012"
source_pdf: "[[raw/papers/traffic-classification-evolution/2020-Lotfollahi-Deep-Packet-Encrypted-Traffic-Classification-SoftComputing-arXiv1709.02656.pdf]]"
tags:
  - 加密流量分类
  - 原始字节表示
  - 报文级判定
  - 类型/论文
key_finding: "把单个 IP 报文截断／补零到 1500 字节向量直接喂给一维 CNN 与栈式自编码器，在 ISCX VPN-nonVPN 上同时完成流量表征与应用识别，是原始字节端到端表示路线的奠基工作之一。"
method: "单报文 → 1500 字节定长向量 → 1D-CNN 与 SAE 两种网络"
aliases:
  - Deep Packet
  - Lotfollahi2020
related:
  - "[[2019-Rezaei-Liu-加密流量深度学习综述]]"
  - "[[2022-Lin-ET-BERT-加密流量预训练]]"
---

# Deep Packet: A Novel Approach For Encrypted Traffic Classification Using Deep Learning

> Lotfollahi 等, 2020, Soft Computing 24(3):1999-2012 · 本机为作者预印本 arXiv:1709.02656（Soft Computing 手稿版式，13 页）
> DOI `10.1007/s00500-019-04030-2`
> **注**：arXiv 版与期刊版中间两位作者顺序不同，正式引用以期刊版为准。

## 一句话

它把"输入就是报文原始字节"这件事做成了完整流水线，也因此把该路线的观测条件写死了。

## 方法核心（含本课题最关心的输入形态）

- **判定单元是单个报文**，不是流，也不是实体（p.2 §贡献列表）。
- **输入构造**（p.6，第 39、48、54、57 行）：
  ISCX VPN-nonVPN 中绝大多数报文的载荷长度小于 `1480` 字节，
  以太网 MTU 为 `1500` 字节，因此作者在固定长度处**截断或补零**，
  得到 `1500` 字节向量作为神经网络输入。
- 预处理会去掉三次握手等无载荷段（p.6 第 6 行）。
- 两种网络：一维 CNN 与栈式自编码器。
- 任务：流量表征（FTP／P2P 等大类）与应用识别（BitTorrent／Skype 等），
  并区分 VPN 与非 VPN。

## 短板（1.2.1「主动排除原始字节路线」段的核心证据）

1. **观测条件**：p.6 的 1500 字节输入构造要求逐报文原始字节可得。
   本课题数据为 NetFlow 记录，无报文字节，该路线在本课题观测条件下**不可实现**，
   这是排除理由中最硬的一条。
2. **判定单元**：报文级判定与运维可处置的实体（主机、通信对）之间还差两级聚合，
   论文未处理该聚合。
3. **数据集单一**：全部结论建立在 ISCX VPN-nonVPN 上（p.3 第 45 行自陈该数据集上
   已有大量工作），无跨数据集或跨时间评价。

## 与相关工作的关系

Deep Packet 之后，ET-BERT、YaTC、NetMamba 等预训练模型沿用同一输入前提
（原始字节／载荷）并把规模放大，因此它们继承了第 1 条观测条件约束。
参见 [[2025-Beltiukov-网络基础模型内在评测批评]] 对该继承代价的实测。
