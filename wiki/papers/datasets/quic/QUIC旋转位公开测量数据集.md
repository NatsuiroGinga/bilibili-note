---
title: "QUIC 旋转位公开测量数据集"
authors: [Ike Kunze, Constantin Sander, Klaus Wehrle]
year: 2023
date: 2026-08-03
journal: "ACM IMC 2023"
source_pdf: "[[raw/papers/datasets/quic/Does-It-Spin-QUIC-Spin-Bit-IMC-2023.pdf]]"
tags:
  - QUIC
  - 旋转位
  - 往返时延
  - qlog
  - 数据集
  - 类型/论文
aliases:
  - Does It Spin 数据集
  - Kunze2023-SpinBit
key_finding: "17.7 GB 数据给出端点 qlog RTT、收发时间、旋转位和包号，适合验证被动 RTT 估计；它缺 ACK、端点丢包、在途字节和拥塞窗口，只能评为 B。"
---

# QUIC 旋转位公开测量数据集

## 一句话

该数据能回答“从加密 QUIC 的旋转位能否测 RTT”，不能回答完整 QUIC 恢复与拥塞动力学。

## 数据内容

作者使用支持 QUIC v1 和多种草案版本的修改版 `zgrab2` 与 `quic-go` 测量网站，并用端点 qlog RTT 作为参考。Zenodo 归档 `extracted-spin-bit-values.tar.gz` 为 17.7 GB，逐行字典包含：

- `QlogRTTs`：QUIC 栈提供的 RTT；
- `SentSpinBits`：发送时间、旋转位值和包号；
- `RecvSpinBits`：接收时间、旋转位值和包号。

论文发现旋转位只在部分 QUIC 目标启用；对启用连接，约 30.5% 的估计较准确，约 51.7% 明显高估。

## 对 R2 的作用

可作为 RTT 可观测性和重排序敏感性的诊断数据，验证“被动状态估计不等于端点真值”。由于缺少 ACK 范围、端点丢包宣告、在途字节和拥塞窗口，它不能承担完整动力学教师，也不值得为当前主线下载 17.7 GB。

## 不可声称

- 包号加收发时间不等于完整确认关系。
- qlog RTT 一项不等于完整 qlog。
- 旋转位性能异常不是恶意标签。

## 文献信息

- DOI：<https://doi.org/10.1145/3618257.3624844>
- 数据 DOI：<https://doi.org/10.5281/zenodo.8305843>

