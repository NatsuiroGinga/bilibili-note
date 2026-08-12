---
title: "snlucsb/netFound-base：netFound 中号预训练权重"
authors:
  - snlucsb (SNL-UCSB)
year: 2026
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/snlucsb/netFound-base"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - netFound
  - 流量基础模型
key_finding: "174.7M 参数、MIT 许可的 netFound 中号权重，下载量仅 49，是 small 与 large 之间的规模消融点。"
---

# snlucsb/netFound-base

## 一句话

netFound 规模阶梯的中间档，用于"骨干规模 vs 迁移收益"的规模消融。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 参数量 174.7M；架构标识 `netFound`；权重格式 `safetensors`。
- 许可证 `mit`。
- 最后更新 2026-03-09；下载量 49，likes 1。

## 与本课题的关系

- 与 small（53.4M）、large（662.2M）构成 3 点规模曲线，可回答"RWKV 机制注入的收益是否随骨干规模衰减"。
- 174.7M 在 RTX 5090（32GB）上可做全参微调，无需分片。

## 待验证

- 三个规模是否用同一预训练语料与同一步数训练（若不同，规模消融不成立）（待验证）。
- 具体层数/隐藏维度需读 `config.json`（待验证）。
