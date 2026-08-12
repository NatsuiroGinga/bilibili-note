---
title: "fla-hub/rwkv7-1.5B-world：RWKV-7 世界模型 1.5B HF 版权重"
authors:
  - fla-hub (flash-linear-attention)
  - Bo Peng（基座 BlinkDL/rwkv-7-world）
year: 2025
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/fla-hub/rwkv7-1.5B-world"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - RWKV
  - RWKV7
key_finding: "1527.4M 参数、Apache-2.0、transformers 可直接 AutoModelForCausalLM 加载（custom_code），下载量 13.1K；是本课题 RWKV 骨干与状态核代码的首选来源。"
---

# fla-hub/rwkv7-1.5B-world

## 一句话

RWKV-7 目前最易接入 HF 生态的 1.5B 权重，Apache-2.0，可直接当骨干或状态核参考实现。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 参数量 1527.4M；架构标识 `rwkv7`；模型类 `AutoModelForCausalLM`；`safetensors`。
- 许可证 `apache-2.0`；语言标签 en/zh/ja/ko/fr/ar/es/pt。
- 依赖 `custom_code`（`trust_remote_code=True`），实现来自 flash-linear-attention。
- 下载量 13.1K，likes 9；最后更新 2025-05-07。
- 基座 `BlinkDL/rwkv-7-world`（finetune 关系）；关联论文 arXiv:2503.14456（RWKV-7 Goose，见 [[wiki/papers/rwkv/2025-Peng-RWKV7-Goose]]）。

## 与本课题的关系

- 若走"取基础模型骨干 + 注入 RWKV 核心机制"，本仓库同时提供两种用法：直接当 RWKV 骨干，或抽取其 `rwkv7` 层实现（广义 Delta 规则状态更新）注入到 Transformer 骨干里。
- Apache-2.0 与 custom_code 组合意味着可以合法修改并发布衍生实现。
- 1.5B 在单张 RTX 5090 上做 LoRA 微调可行，全参微调需实测（待验证）。
- 注意：这是语言模型权重，词表与流量字节/字段 token 不匹配，直接迁移前需重建 embedding 或做 token 对齐。

## 待验证

- `custom_code` 内核对 CUDA 12.8 / Blackwell（sm_120）的兼容性（fla 的 Triton 内核版本要求）（待验证，需实测）。
- 1.5B 在 5090 上的训练显存与吞吐（待验证）。
