---
title: "QUIC-MedNetCom：蜂窝网络中的 QUIC 拥塞控制 qlog 数据集"
authors: [Mohamed Moulay, Fernando Díez Muñoz, Vincenzo Mancuso]
year: 2021
date: 2026-08-03
journal: "IEEE MedComNet 2021"
source_pdf: "[[raw/papers/datasets/quic/Experimental-Assessment-QUIC-Congestion-Control-Cellular-2021.pdf]]"
tags:
  - QUIC
  - qlog
  - 拥塞控制
  - 蜂窝网络
  - 数据集
  - 类型/论文
aliases:
  - QUIC-MedNetCom
  - Moulay2021-QUIC
key_finding: "公开仓库含 89 个 qlog；通过字段门禁的迹线同时提供包号、ACK、端点丢包、RTT、在途字节和拥塞窗口，是目前最适合 R2 的公开动力学教师，但数据较旧且没有攻击标签。"
---

# QUIC-MedNetCom：蜂窝网络中的 QUIC 拥塞控制 qlog 数据集

## 一句话

这是本轮检索中动力学字段最完整、体量又可控的公开来源，适合提供训练期端点状态监督，不适合独立承担恶意流量分类。

## 数据与方法

论文在 MONROE 商用蜂窝网络平台上运行 Flowsim 和 Mvfst，比较 BBR、COPA、Cubic、NewReno 等拥塞控制器及移动/静态场景。官方仓库 `Mohmoulay/QUIC-MedNetCom` 当前核验提交为 `f237a20360b83868a197488c5b557f53e4b7e53c`。

仓库受 Git 跟踪的 201 个文件合计 695,847,552 字节，其中 89 个 `.qlog` 合计 630,227,334 字节。样本使用旧 qlog 草案格式，并存在 `.json` 与 `.qlog` 同内容副本。

## 字段核验

- 小样本同时出现包号、ACK、往返时延、在途字节和拥塞窗口。
- 抽检的丢包样本含 5 个端点 `recovery:packet_lost` 事件，给出丢失包号和重排序阈值触发原因。
- 包类型能区分 Initial、Handshake 和 1-RTT；部分旧模式不显式写 `packet_number_space`，必须结合包类型归一化。
- 不同实现、场景和文件的字段完整性不一致，不能因扩展名为 qlog 就自动纳入。

## 对 R2 的作用

可用于监督历史状态辨识器，验证 ACK 到达、RTT 更新、在途字节变化和丢包后的拥塞响应。端点私有字段必须只用于训练期教师或状态损失，推理输入仍保持可部署的包长、方向、时间及协议可见字段。

建议先按场景、实现和控制器分层选取 20—50 条轨迹，逐条通过字段门禁，预计占用 0.15—0.35 GiB；不必先拉取或解析全部副本。

## 局限与不可声称

- 数据主要来自 2020 年前后的 QUIC draft-27，不代表现代 QUIC v1 的全部行为。
- 没有恶意/良性或攻击类别标签。
- 仓库根目录没有明确的数据许可，论文公开不等于数据可任意再发布。
- 不能把蜂窝性能异常直接写成网络攻击。

## 待验证

1. 建立每条 qlog 的字段完整性、实现、控制器、地区和场景 manifest。
2. 向作者确认数据许可和再分发边界。
3. 用现代 Interop 轨迹量化旧草案到 QUIC v1 的迁移偏差。

## 文献信息

- DOI：<https://doi.org/10.1109/MEDCOMNET52149.2021.9501271>
- 官方仓库：<https://github.com/Mohmoulay/QUIC-MedNetCom>

