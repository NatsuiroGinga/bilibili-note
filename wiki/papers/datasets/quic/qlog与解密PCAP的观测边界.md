---
title: "qlog 与解密 PCAP 的 QUIC 观测边界"
authors: [Robin Marx, Wim Lamotte, Peter Quax]
year: 2020
date: 2026-08-03
journal: "ACM SIGCOMM 2020"
source_pdf: "[[raw/papers/datasets/quic/Visualizing-QUIC-and-HTTP3-with-qlog-and-qvis-2020.pdf]]"
tags:
  - QUIC
  - qlog
  - PCAP
  - 拥塞控制
  - 类型/论文
aliases:
  - qlog 与 qvis
  - Marx2020-qvis
key_finding: "qlog 能记录端点内部的 RTT、拥塞窗口、在途字节和丢包判定；解密 PCAP 只能重建线上包帧，因此两者不能在物理残差监督中互换。"
---

# qlog 与解密 PCAP 的 QUIC 观测边界

## 一句话

解密 PCAP 告诉研究者“线上传了什么”，端点 qlog 还能告诉研究者“协议栈认为发生了什么”，完整动力学监督需要后者。

## 核心机制

论文介绍 qlog 的端点事件记录和 qvis 的序列、拥塞、复用及分包视图。端点可记录包发送/接收、ACK、RTT 估计、拥塞窗口、在途字节和丢包恢复状态。PCAP 配合 TLS 密钥能恢复受保护的 QUIC 帧，但无法可靠重建本地定时器、拥塞控制器内部状态或端点首次判丢时刻。

当前 IETF qlog 事件定义继续覆盖 `packet_sent`、`packet_received`、`packets_acked`、`recovery_metrics_updated`、`timer_updated` 和 `packet_lost` 等事件，但许多字段仍是可选项。

## 对 R2 的直接约束

1. 数据集有 qlog 只是候选条件，必须逐迹线检查核心字段。
2. H23Q、VisQUIC 等 PCAP 加密钥数据只能提供线上可观测残差和攻击标签。
3. MedNetCom、Interop、EPIQ 的端点 qlog 才能提供训练期私有状态教师。
4. 推理期不能要求部署环境产生 qlog，否则方法不再是仅基于网络流量的检测。

## 文献信息

- DOI：<https://doi.org/10.1145/3405837.3412356>
- 作者页面：<https://qlog.edm.uhasselt.be/>
- IETF qlog：<https://quicwg.org/qlog/>
