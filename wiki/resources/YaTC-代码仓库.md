---
title: "NSSL-SJTU/YaTC：掩码自编码流量 Transformer 代码仓库"
authors:
  - NSSL-SJTU（上海交通大学）
year: 2023
date: 2026-08-08
journal: "GitHub 代码仓库（AAAI 2023）"
resource_type: 代码仓库
url: "https://github.com/NSSL-SJTU/YaTC"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - YaTC
  - 掩码自编码
key_finding: "AAAI 2023 论文代码，但无 LICENSE 文件、最后提交 2024-04-29 已停更两年、依赖仅声明 torch=1.9.0、权重与数据全部走 Google Drive，复现与合规风险都高。"
---

# NSSL-SJTU/YaTC

## 一句话

AAAI 2023 的 MAE 式流量 Transformer，学术分量足但工程可复现性最弱。

## 实测事实（GitHub API + README，核验日期 2026-08-08）

- 许可证：GitHub API 返回 `None`——**无 LICENSE 文件**。
- 最后提交 2024-04-29T17:05:07Z，信息 `Update data_process.py`；停更约 2 年；未归档；Stars 156。
- 依赖：README 依赖段列 `torch=1.9.0`，**未声明 CUDA 版本**。
- 权重分发：Google Drive（README "Pre-trained model Link"）；数据分发：Google Drive，含 4 个流量数据集，类别数 7—20。
- 输入形态：pcap 流 → **MFR 矩阵（Multi-level Flow Representation）**，不是普通流量灰度图。README 原文表述为把 pcap 流转成 MFR matrices。
- 论文：AAAI 2023，《Yet Another Traffic Classifier: A Masked Autoencoder Based Traffic Transformer with Multi-Level Flow Representation》，2023-02-07—14，Washington。

## 与本课题的关系

- MFR 多层次流表示是"把报文头与载荷分层排布成二维矩阵"的代表做法，与本课题关心的"跨字段交互机制"直接相关：MFR 用二维卷积/patch 位置隐式编码字段位置，而非显式字段嵌入。
- 类别数仅 7—20 的数据集规模，说明其评测任务粒度粗，难以支撑"基础模型"的泛化主张。
- torch 1.9.0 与 RTX 5090 完全不兼容（sm_120 需 CUDA 12.8+），复现需整体重建（阻塞项）。

## 负面信息

- 无许可证，衍生使用有法律风险。
- 权重与数据均在 Google Drive，无 DOI 与校验和。
- 停更两年，issue 响应状况未核（待验证）。

## 待验证

- 4 个数据集的具体名称与划分方式，是否存在按包而非按流划分导致的泄漏（待验证，需读论文与 data_process.py）。
- Google Drive 链接当前有效性（待验证）。
