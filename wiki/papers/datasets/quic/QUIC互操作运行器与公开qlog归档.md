---
title: "QUIC 互操作运行器与公开 qlog 归档"
authors: [Marten Seemann, Jana Iyengar]
year: 2020
date: 2026-08-03
journal: "ACM EPIQ 2020"
source_pdf: "[[raw/papers/datasets/quic/Automating-QUIC-Interoperability-Testing-Seemann-Iyengar-2020.pdf]]"
tags:
  - QUIC
  - qlog
  - 互操作测试
  - 数据集
  - 类型/论文
aliases:
  - QUIC Interop Runner
  - Seemann2020-Interop
key_finding: "互操作运行器能在受控丢包、黑洞、损坏和跨流场景下产生双端日志、PCAP、密钥与 qlog；现代归档样本具备完整动力学字段，但归档滚动且没有冻结清单。"
---

# QUIC 互操作运行器与公开 qlog 归档

## 一句话

它不是传统固定数据集，而是持续运行的 QUIC 实现互操作实验基础设施；冻结指定运行和文件哈希后，可作为现代 QUIC 动力学补充。

## 数据来源

官方仓库提供测试编排，公开归档 `interop.seemann.io/quic` 按运行时间、实现和场景保存客户端/服务端日志、模拟器 PCAP、TLS 密钥及实现可选的 qlog。场景包括传输丢包、握手丢包、黑洞、包损坏、重绑定、迁移和跨流量等。

## 实测字段

抽检普通样本约 3.7 MB，包含包号、ACK 范围、RTT、在途字节和拥塞窗口。抽检 `transferloss` 服务端 qlog 约 1.31 MB，包含：

- 68 个 `recovery:packet_lost` 事件；
- 2437 次恢复指标更新，其中 2436 次含在途字节；
- 793 次平滑 RTT 更新；
- 132 次拥塞窗口更新；
- 850 个 ACK 范围和 1558 个包号空间记录。

这证明特定实现和场景能达到 A 级，但不是所有归档文件都一定包含相同字段。

## 对 R2 的作用

优先冻结 20—40 条现代 QUIC v1 轨迹，覆盖正常、丢包、跨流和路径变化，用来检查旧 MedNetCom 教师在当前协议实现上的适用性。每条轨迹必须记录运行时间、端点实现、测试名、文件 URL、SHA-256、qlog 模式版本和字段门禁结果。

## 局限与不可声称

- 归档滚动变化，没有官方总容量和固定 DOI。
- 公开页面不等于数据许可；代码的 MIT 许可不能自动覆盖所有实现上传的日志。
- 没有恶意标签，受控丢包也不能直接等同攻击。
- 不能用今天网页上的路径代替论文可复现实验 manifest。

## 文献信息

- DOI：<https://doi.org/10.1145/3405796.3405826>
- 官方仓库：<https://github.com/quic-interop/quic-interop-runner>
- 公开归档：<https://interop.seemann.io/quic>

