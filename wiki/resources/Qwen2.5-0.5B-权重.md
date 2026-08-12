---
title: "Qwen/Qwen2.5-0.5B：小规模 Transformer 基座对照"
authors:
  - Qwen Team, Alibaba
year: 2024
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/Qwen/Qwen2.5-0.5B"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - Qwen
  - 基线骨干
key_finding: "494.0M 参数、Apache-2.0、下载量 27.2M 的成熟小基座；是注入 RWKV 机制实验中同规模 Transformer 对照的最稳妥选择。"
---

# Qwen/Qwen2.5-0.5B

## 一句话

工程成熟度最高的 0.5B 级开源基座，作为 attention 对照组与"机制注入"的宿主骨干。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 参数量 494.0M；架构 `qwen2`；模型类 `AutoModelForCausalLM`；`safetensors`。
- 许可证 `apache-2.0`；语言 en。
- 下载量 27.2M，likes 435；最后更新 2024-09-25。关联论文 arXiv:2407.10671。
- 标签含 `text-generation-inference`、`endpoints_compatible`，**不需要** `custom_code`。

## 与本课题的关系

- 本课题构思是"取基础模型骨干，把 RWKV 核心机制注入进去"。Qwen2.5-0.5B 是被注入的宿主候选：原生 transformers 支持、无 remote code、生态工具（LoRA/量化/推理）齐全，改造后的差异可以干净地归因到注入的机制。
- 494.0M 与 netFound-large(662.2M)、rwkv7-1.5B 构成跨架构规模可比区间。
- 作为纯 attention 基线，回答"线性状态是否真的必要"。

## 与已测结论的交叉

- 已测 LSPR24 5 秒窗口有效历史约 20 秒（4 窗），长历史池化仅 +14.1% 未达门槛。在这种短有效历史下，attention 的二次复杂度并不构成瓶颈——用 Qwen2.5-0.5B 做对照可以直接检验"RWKV 的长程优势在本任务上是否有用武之地"。这是本路线最需要先证伪的假设。

## 待验证

- 词表/tokenizer 对流量字段序列的适配方式（重建 embedding 还是字节级重编码）（待验证）。
