---
title: "Sizing Router Buffers：带宽时延积定容的适用边界"
authors: [Guido Appenzeller, Isaac Keslassy, Nick McKeown]
year: 2004
date: 2026-08-05
journal: "ACM SIGCOMM 2004"
source_pdf: "[[raw/papers/pinn/pcap/2004-Appenzeller-路由器缓存定容.pdf]]"
sha256: "c35cdb294b960f0aabaa06c246f21868a1357cd9b531be06d49c562f36866181"
key_finding: "带宽时延积是少量同步 TCP 长流维持链路利用率时的经验规则；多条独立长流下建议值约按流数平方根缩小，不能直接当作单流 QUIC 用户态代理的容量定律。"
tags:
  - 路由器缓存
  - 带宽时延积
  - 队列定容
  - 类型/论文
aliases:
  - Sizing Router Buffers
  - Appenzeller2004
related:
  - "[[LeBoudec-Thiran-网络演算队列边界]]"
---

# Sizing Router Buffers：带宽时延积定容的适用边界

## 一句话

`RTT × C` 不是所有队列的物理容量公式；它来自特定 TCP 多路复用和吞吐保持问题，不能直接证明单连接用户态 QUIC 代理需要多大缓存。

## 论文原结论

- 传统经验将路由器缓冲区取为链路容量与典型往返时延之积。
- 对大量相互独立、长期存在的 TCP 流，论文提出缓冲需求可近似缩小为 `RTT × C / √N`。
- 该结论围绕路由器输出端口、TCP 窗口同步和链路利用率展开，不是应用层或用户态转发器的逐事件无丢包定容模型。

## 对 R2 的直接约束

- 当前 `20 Mbit/s × 100 ms` 的带宽时延积约为 `250000` 字节；`2 MiB` 约为其 `8.39` 倍。
- 这个对比只说明 `2 MiB` 是较宽松的工程上限，不能把它写成由带宽时延积推导出的物理真值。
- 若目标是用户态代理零丢包，应优先使用开发到达包络与服务曲线定容，而不是搬用路由器吞吐规则。

## 本课题推论

`2 MiB` 可以在一次有明确终点的修复实验中保留为预注册硬上限，用于排除代理容量不足；论文中必须将其描述为实验工程参数，并报告相对于带宽时延积和观测突发峰值的倍数。

## 不能推出

- 论文不支持 `80%` 余量门禁。
- 论文不支持把 QUIC、TCP 和 UDP 的用户态代理统一按一个带宽时延积公式定容。

## 待实验验证

- 修正端点发送节奏后，观测峰值相对于 `250000` 字节带宽时延积的倍数。
- 使用更小的预注册容量时，吞吐、排队时延和丢包是否发生可解释变化。

## 文献信息

- DOI：https://doi.org/10.1145/1015467.1015499
- 作者公开原件：https://tiny-tera.stanford.edu/~nickm/papers/sigcomm2004-extended.pdf

