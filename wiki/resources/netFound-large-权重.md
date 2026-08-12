---
title: "snlucsb/netFound-large：netFound 大号预训练权重"
authors:
  - snlucsb (SNL-UCSB)
year: 2026
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/snlucsb/netFound-large"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - netFound
  - 流量基础模型
key_finding: "662.2M 参数、MIT 许可的 netFound 最大号公开权重；注意它与 netFound-640M-base（711.8M）不是同一检查点。"
---

# snlucsb/netFound-large

## 一句话

当前 netFound 家族公开权重的规模上限，MIT 许可，可作最强流量基础模型基线。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 参数量 662.2M；架构标识 `netFound`；`safetensors`。
- 许可证 `mit`。
- 最后更新 2026-03-09；下载量 46，likes 1。
- 与 `snlucsb/netFound-640M-base` 是**两个不同仓库**：后者架构标识为 `NetFound`（大小写不同）、无 license 元数据、更新于 2026-04-27，且模型卡自称属于已被取代的 v1。

## 与本课题的关系

- 662.2M 全参微调在单张 RTX 5090 上需要梯度检查点或 LoRA，直接全参训练的显存预算需实测。
- 作为"最强 Transformer 流量基础模型"基线，用于对照 RWKV 机制注入后的线性复杂度收益。

## 待验证

- 单卡 5090 全参微调的实际显存与吞吐（待验证，需实测）。
- large 与 640M-base 的关系（是否 v2 重训版本）（待验证）。
