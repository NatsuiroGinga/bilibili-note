---
title: "XTab: Cross-table Pretraining for Tabular Transformers"
authors: [Bingzhao Zhu, Xingjian Shi, Nick Erickson, Mu Li, George Karypis, Mahsa Shoaran]
year: 2023
date: 2026-09-03
journal: "ICML 2023；arXiv:2305.06090"
source_pdf: "[[raw/papers/methodology/2023-Zhu-XTab-Cross-Table-Pretraining.pdf]]"
sha256: "dcc499005ec765512529998d8c73d5806d2b5ec29ba0031dcd0731c55d79f1e0"
tags:
  - 表格数据
  - FT-Transformer
  - 跨表预训练
  - 联邦学习
  - 训练协议
  - 类型/论文
key_finding: "XTab 以联邦学习跨 52 个 AMLB 表预训练共享 Transformer 骨干（默认即 Gorishniy et al. 2021 的 FT-Transformer 配置：3 块、嵌入 192、8 头），预训练与微调两阶段均使用 AdamW、学习率 1e-4、权重衰减 1e-5，逐字沿用 Gorishniy 2021 的默认优化器配方，全文未提及任何学习率调度器（物理页 5-6，§4.2）。"
method: "联邦式跨表预训练：各表用独立 featurizer，共享 Transformer 骨干参数按 FedAvg 风格跨表同步；下游微调随机初始化新 featurizer 与预测头，仅迁移预训练骨干"
baseline: "同结构随机初始化 FT-Transformer（无预训练基线）、Fastformer、Saint-v、TransTab、树模型与 AutoGluon 神经网络"
aliases:
  - XTab
  - Zhu2023-XTab
related:
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
  - "[[2025-Gorishniy-TabM参数高效集成]]"
---

# XTab：表格 Transformer 的跨表预训练

> Zhu、Shi、Erickson、Li、Karypis、Shoaran，ICML 2023，arXiv:2305.06090，物理页 1 至 24。

**核对说明**：本仓库 `thesis/methods/表格预训练模型可行性调研.md` 此前把末位作者记为 "Shah"，经本次全文核验，PDF 首页实际作者为 **Mahsa Shoaran**，非 Shah；该处系此前转述笔误，本笔记以现场核验为准。

## 一句话

XTab 的骨干**就是 FT-Transformer**（§4.2 明确"与 Gorishniy et al. 2021 相同：3 个 Transformer 块、嵌入维度 192、8 个注意力头"），其训练协议（AdamW、lr=1e-4、wd=1e-5、无调度器）逐字沿用 Gorishniy 2021 的默认配方，预训练与微调两阶段均不例外。

## 训练协议（本次核查重点，逐句带页码）

- 模型配置（物理页 5，§4.2）："Our default model configuration of transformer variants is the same as Gorishniy et al. (2021), with 3 transformer blocks, a feature embedding size of 192 and 8 attention heads."
- 微调设置（物理页 5，§4）：
  - **Light finetuning**：固定 3 个 epoch（"finetune XTab for a fixed number of epochs (3 epochs)"）。
  - **Heavy finetuning**：早停耐心 3 个 epoch，最大轮数设为无穷（"early stopping patience of 3 epochs. The maximum number of epochs is set to infinity"）。
  - 附录 I.4 另有 **FTT-best/XTab-best**：早停耐心 20，每 0.5 epoch 存一次检查点，取验证最优的前 3 个检查点做 model soup（物理页 20-21，Table 10；`val_check_interval=0.5`、`top_k=3`）。
- 优化器（物理页 6，§4.2 正文）：**"The batch size is fixed at 128 for both pretraining and finetuning. Both stages use AdamW as the optimizer, with a learning rate of 1e-4. Following Gorishniy et al. (2021); Rubachev et al. (2022), we also apply a weight decay of 1e-5 to all components excluding featurizers, [CLS] tokens, layer normalization and bias terms."** ——批量 128、AdamW、lr=1e-4、wd=1e-5（分词器/[CLS]/层归一化/偏置除外），显式标注沿袭 Gorishniy 2021 与 Rubachev 2022（即本课题 `2022-Gorishniy-表格深度学习数值特征嵌入.md` 笔记对应论文）。
- **全文检索零命中"schedul"**（含 scheduler/schedule 各种形式），两个 PDF 分段文件（物理页 1-20、21-24）合计检索无一处提及学习率调度器；同样零命中 warmup、cosine、StepLR 等关键词。
- Table 10（物理页 21，附录 I.4，FTT/XTab 超参表）：`num_epochs=inf`、`early_stop_patience=20`、`num_blocks=3`、`hidden_size=192`、`num_attention_heads=8`、`batch_size` 默认 128（HPO 空间 `[128,32,8,1]`）——表中未单列 learning_rate 行，因其已在正文（物理页 6）固定为 1e-4。

## 训练不稳定性：未见报告

全文检索 instab/oscillat/diverg/unstable/spike/loss spike 均无命中。唯一讨论的"性能随训练预算变化"现象是**灾难性遗忘**（catastrophic forgetting），不是数值震荡：重构目标下 light finetuning 胜率 71.0%，heavy finetuning 降至 56.1%（物理页 5-6，§4.3），作者将其归因于 FT-Transformer 骨干参数量小（<1M）、微调期容易遗忘预训练知识（引 Ramasesh et al. 2021; Kaushik et al. 2021），与学习率调度无关。**本文不能作为"无调度器导致训练震荡"或"无调度器不会导致训练震荡"任一方向的证据**——它只是没有讨论这个问题维度。

## 证据等级

- 原件级别：完整论文，24 个物理页，PDF 从 arXiv 直接下载（2026-09-03），MinerU flash-extract 两段转换（物理页 1-20、21-24）+ 单页核验定位精确页码（物理页 5、6）。
- 可支撑：XTab 预训练与微调阶段的优化器超参数（AdamW、lr=1e-4、wd=1e-5）逐字沿用 Gorishniy 2021 默认配方；全文未提及学习率调度器。
- 不可支撑：训练稳定性/震荡与学习率调度的因果关系——本文未讨论该问题。
