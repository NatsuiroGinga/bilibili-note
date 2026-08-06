---
title: "RFC 9002：QUIC 丢失检测、拥塞控制与发送节奏"
authors: [Jana Iyengar, Ian Swett]
year: 2021
date: 2026-08-05
journal: "RFC Editor，RFC 9002"
source_pdf: "[[raw/papers/pinn/protocol-adaptive/2021-RFC9002-QUIC丢失检测与拥塞控制.pdf]]"
sha256: "d01a2adb6a0221ac152d96e2bfe65dc817ef0ee7d2a50c62861414caa3bf8260"
key_finding: "QUIC 发送端应对在途分组进行节奏控制或限制突发；最大数据报是路径和配置约束，不是 UDP 接收缓冲大小。"
tags:
  - QUIC
  - 拥塞控制
  - 发送节奏
  - 类型/论文
aliases:
  - RFC9002
  - QUIC Loss Detection and Congestion Control
related:
  - "[[RFC9000-QUIC传输与旋转位边界]]"
---

# RFC 9002：QUIC 丢失检测、拥塞控制与发送节奏

## 一句话

QUIC 的拥塞控制状态以字节计量，发送端必须通过节奏控制或突发限制避免瞬时拥塞；用户态代理若忽略端点给出的发送时刻，会把实现缺陷误记成网络动力学。

## 规范原结论

- 第 7.2 节给出初始拥塞窗口：通常为 `10 × max_datagram_size`，并设有上下界；`max_datagram_size` 不包含 UDP/IP 首部开销，而是由路径最大传输单元和实现配置决定。
- 第 7.7 节指出，不加延迟连续发送多个分组会形成突发并造成短时拥塞或丢包。发送端应对在途分组进行节奏控制；若不使用节奏控制，则必须限制突发大小。
- 附录 A 的恢复伪代码把拥塞窗口、在途字节和已发送字节作为独立状态，不能由代理队列长度替代。

## 对 R2 的直接约束

- `max_datagram_bytes` 必须从端点配置和实际发包审计得到，不能把 `recv()` 缓冲区的 `65535` 字节当作数据报上限。
- quiche 与 aioquic 的发送节奏是否实际生效必须写入运行凭据，包括计划发送时刻、实际到达间隔和系统调度路径。
- 代理的等待队列、正在串行化的字节、传播中的字节和 QUIC 端点的在途字节是四种不同状态，不能合并成一个 `backlog`。

## 本课题推论

若 quiche 示例程序没有兑现 `SendInfo.at`，而 aioquic 的异步协议循环兑现了内部计时器，两者会产生不同的入队突发。这个差异可以解释 v3 中实现相关的排队现象，但只有逐事件到达间隔和发送时刻证据才能判定它是否是具体失败的原因。

## 不能推出

- 规范没有规定用户态代理必须使用 `2 MiB` 队列，也没有规定峰值占用必须低于 `80%`。
- 传输完成不代表代理没有隐藏丢包或错误排队；QUIC 的重传机制可能掩盖代理丢包。

## 待实验验证

- quiche 端点是否真正启用了 `SO_TXTIME`、`ETF` 队列或用户态定时器。
- 两种实现的观测最大 UDP 数据报是否分别不超过冻结配置值。
- 修正发送节奏后，v3 的 quiche 特有突发是否消失。

## 文献信息

- DOI：https://doi.org/10.17487/RFC9002
- 官方页面：https://www.rfc-editor.org/info/rfc9002

