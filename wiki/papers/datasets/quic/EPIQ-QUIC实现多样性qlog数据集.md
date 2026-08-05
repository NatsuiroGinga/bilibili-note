---
title: "EPIQ 2020：QUIC 与 HTTP/3 实现多样性 qlog 数据集"
authors: [Robin Marx, Joris Herbots, Wim Lamotte, Peter Quax]
year: 2020
date: 2026-08-03
journal: "ACM EPIQ 2020"
source_pdf: "[[raw/papers/datasets/quic/Same-Standards-Different-Decisions-QUIC-Implementation-Diversity-2020.pdf]]"
tags:
  - QUIC
  - HTTP3
  - qlog
  - 实现多样性
  - 数据集
  - 类型/论文
aliases:
  - EPIQ 2020 数据集
  - Marx2020-Diversity
key_finding: "EPIQ 公开 15 种 QUIC/HTTP3 实现的原始 qlog，部分轨迹含完整恢复状态；其价值在实现差异和旧模式兼容，不在现代攻击检测。"
---

# EPIQ 2020：QUIC 与 HTTP/3 实现多样性 qlog 数据集

## 一句话

EPIQ 能检验同一标准在不同实现中的 ACK、包号空间、拥塞控制和分包差异，但使用 draft-25 至 draft-27，不能替代现代 QUIC 主数据。

## 数据内容

论文比较 15 种实现，覆盖流量与拥塞控制、0-RTT、多路复用、分包、传输参数、ACK 行为、包号空间、包合并和路径最大传输单元发现。官方 ZIP 实测 19,057,641 字节，解压 331,166,430 字节，共 64 项，通过完整性检查。

抽检 Firefox qlog 包含包号、ACK、丢包、RTT 和在途字节，但缺拥塞窗口。抽检 quic-go qlog 同时包含包号、ACK、92 个丢包事件、丢包定时器、RTT、在途字节、拥塞窗口和包号空间。由此只能把通过逐文件门禁的子集判为 A。

## 对 R2 的作用

- 验证 qlog 模式适配器能否处理不同实现和旧格式。
- 检查物理状态辨识是否过拟合单一实现的记录习惯。
- 作为诊断集，而不是训练或最终外部测试的主结果。

## 局限与不可声称

- 无攻击标签。
- 协议版本早于 RFC 9000，字段名称和语义存在漂移。
- 官方页没有单列数据许可。
- 不能把实现差异误写成恶意行为。

## 文献信息

- DOI：<https://doi.org/10.1145/3405796.3405828>
- 官方页面：<https://qlog.edm.uhasselt.be/epiq/>
- 数据：<https://qlog.edm.uhasselt.be/epiq/files/dataset.zip>

