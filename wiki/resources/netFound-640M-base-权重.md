---
title: "snlucsb/netFound-640M-base：netFound v1 大号检查点（参数量口径不一致）"
authors:
  - snlucsb (SNL-UCSB)
year: 2026
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/snlucsb/netFound-640M-base"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - netFound
  - 参数量口径
key_finding: "模型卡自报 643,825,672 参数，HF 元数据显示 711.8M，差约 68M（约 10.6%）；该检查点被作者明确标注为 netFound-v1，已被 v2 家族取代，且仓库无许可证元数据。"
---

# snlucsb/netFound-640M-base

## 一句话

下载量最高（460）但已被作者宣告过时的 netFound v1 检查点，参数量两套口径不一致，引用时必须注明来源。

## 实测事实（HF 模型卡与元数据，核验日期 2026-08-08）

- 模型卡 `## Checkpoint` 段原文：`Model: Large (16 heads, 24 hidden layers, 1024 hidden size)`，`Total params: 643,825,672`，日期 `January 17, 2025`。
- HF 元数据 `Parameters: 711.8M`，架构标识 `NetFound`。**两者相差约 6.8×10⁷（711.8M 相对 643.8M 高 10.6%）**，最可能来源是元数据统计包含了 embedding / MLM 头等模型卡未计入的部分（推论，未证实）。
- 模型卡首行警示：该模型为 netFound-v1 设计，现已被 netFound-v2 家族取代，指向 GitHub 仓库与 `https://huggingface.co/snlucsb/models`。
- **无 license 元数据**（tags 中不含 `license:` 项），与 small/base/large 的 MIT 不同。
- 模型卡自报预训练指标（fill-mask）：Macro MLM F1 0.4038、Weighted MLM F1 0.8451、MLM Accuracy 0.8514、Swapped Weighted F1 0.9605、Perplexity 6.5842。
- 预训练语料：私有真实数据集，>4.5 亿条网络流，训练约 1 个 epoch（约 4.8 亿流）。
- 下载量 460、likes 4，更新于 2026-04-27。对应论文 arXiv:2310.17025。

## 负面信息与口径问题

- Macro MLM F1 仅 0.4038 而 Weighted MLM F1 0.8451：说明掩码预测在长尾 token 上很差，加权指标被高频 token 抬高。引用时不得只报 0.8451。
- 预训练语料私有（450M flows 不公开），预训练阶段不可复现；只有下游微调可复现。
- 该检查点无许可证声明，法律上不可默认当作 MIT 使用。

## 与本课题的关系

- 若要用最大号 netFound 做基线，优先用 MIT 的 `netFound-large`，避免许可证空白。
- 模型卡给出的结构参数（16 heads / 24 layers / 1024 hidden）可直接用于估算 RWKV 状态核注入后的参数与状态开销。

## 待验证

- 711.8M 与 643.8M 的差额构成（需下载 safetensors 索引逐张量求和核对）（待验证）。
- netFound-v2 家族的具体仓库列表与是否覆盖 small/base/large（待验证）。
