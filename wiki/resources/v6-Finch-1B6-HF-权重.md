---
title: "RWKV/v6-Finch-1B6-HF：RWKV-6 Finch 1.6B 官方 HF 版权重"
authors:
  - RWKV（官方组织）
year: 2024
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/RWKV/v6-Finch-1B6-HF"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - RWKV
  - RWKV6
key_finding: "RWKV 官方组织发布的 rwkv6 架构权重，Apache-2.0，下载量 12.7K；但仍标 custom_code、只有 pytorch 格式、HF 元数据未给出参数量，且自 2024-09 未更新。"
---

# RWKV/v6-Finch-1B6-HF

## 一句话

RWKV-6 代际的官方 HF 权重，作为"上一代 RWKV"消融对照，不是当前主线骨干。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 架构标识 `rwkv6`；模型类 `AutoModelForCausalLM`；库 `transformers`；权重格式 `pytorch`（**无 safetensors**）。
- 许可证 `apache-2.0`；标签含 `custom_code`。
- 下载量 12.7K，likes 6；最后更新 2024-09-03。
- HF 元数据**未显示参数量**（名称暗示约 1.6B，为推论）。

## 与本课题的关系

- 用于"RWKV-6 与 RWKV-7 状态更新机制哪种更适合流量序列"的代际消融：RWKV-6 是标量/向量衰减，RWKV-7 是广义 Delta 规则矩阵状态。
- `pytorch` 格式 + `custom_code` 意味着加载需 `trust_remote_code=True` 且存在 pickle 风险，须 `weights_only` 或改用 safetensors 转换。
- 近 2 年未更新，与新版 transformers 的兼容性有风险。

## 待验证

- 实际参数量（需读 config/权重求和）（待验证）。
- 与当前 transformers 版本的兼容性（待验证，需实测加载）。
