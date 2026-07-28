---
title: "LoRA-Switch: Boosting the Efficiency of Dynamic LLM Adapters via System-Algorithm Co-design"
authors:
  - Rui Kong
  - Qiyang Li
  - Xinyu Fang
  - Qingtian Feng
  - Qingfeng He
  - Yazhu Dong
  - Weijun Wang
  - Yuanchun Li
  - Linghe Kong
  - Yunxin Liu
year: 2024
date: 2026-07-22
journal: "arXiv preprint; submitted to ICLR 2025"
source_pdf: "[[raw/papers/pinn/2024-Kong-LoRA-Switch.pdf]]"
tags:
  - 类型/论文
  - 主题/动态适配器
  - 主题/低秩适配
  - 主题/推理效率
key_finding: "LoRA-Switch 发现动态 LoRA 的碎片化内核调用会造成远高于浮点运算量估计的延迟，并以词元预路由和内核融合降低开销；其正式录用状态未核验。"
method: "词元级预路由、Top-2 动态 LoRA、权重预合并、CUDA 内核融合"
baseline: "MOLA、PESC、MoRAL、原始 Llama2-7B"
aliases:
  - LoRA-Switch
  - Kong2024-LoRASwitch
---

# LoRA-Switch 动态适配器切换

> Rui Kong 等，2024，arXiv 预印本与 ICLR 2025 投稿 · PDF 15 页

## 一句话

论文提醒动态低秩专家的推理成本不能只按参数量和浮点运算量估计；但其系统优化不能证明物理路由有效，也不能作为已正式录用成果引用。

## 背景

动态 LoRA 通常只增加 1% 至 5% 参数和不足 1% 的浮点运算量，却因每层多个小矩阵和碎片化 CUDA 内核调用显著拖慢自回归解码。

## 方法核心

LoRA-Switch 在生成当前词元前执行 Top-2 预路由，使本词元各层使用的适配器路径预先确定。系统随后把激活的 LoRA 更新合入基座权重，并用定制 CUDA 内核一次融合多个适配器的合并操作。

它是系统与算法协同设计：路由机制服务于可预合并执行，不是为了物理状态可解释性。

## 实验结果

- 在 Llama2-7B、ShareGPT、逐请求生成 200 个新词元的分析中，原始模型约为 2.4 毫秒/词元；MOLA、PESC、MoRAL 分别约为 25.3、8.5、8.6 毫秒/词元。
- 作者将主要开销归因于额外 CUDA 内核启动，而不是低秩矩阵的理论浮点运算量。
- 论文报告在保持与所比较动态适配器相近准确率提升时，解码延迟降低超过 2.4 倍。

## 发表状态核验

本地 PDF 明确标注“预印本，审稿中”。OpenReview 标识 `NIG8O2zQSQ` 对应 ICLR 2025 投稿页面；DBLP 将其记录为 CoRR `abs/2405.17741`、非正式出版物。本次没有核验到录用决定，因此参考文献不得写成 ICLR 2025 正式论文。

## 我的理解

当前单物理私有适配器只在子类和开放集路径激活，动态性有限，推理成本可直接实测。若未来引入三个物理专家，必须报告首词元与后续词元延迟、吞吐、峰值显存和内核调用，而不能只说激活秩很小。

序列级固定路由比逐词元切换更适合当前四窗口流量输入：一个样本只计算一次物理状态路由，各生成词元沿用同一专家组合，既更可解释也更易测成本。

## 局限与不可外推结论

- 当前公开状态不是正式会议录用，证据等级低于正式论文。
- 依赖定制 CUDA 内核和特定服务场景，不是通用 Python/PEFT 实现即可获得的速度。
- Top-2 词元路由不保证物理语义，也不提供家族分支不变性。
- 2.4 倍是相对所比较动态适配器，不是相对普通单 LoRA 或无适配器基座。

## 与相关工作的关系

- [[MixLoRA词元级低秩专家混合]] 关注训练与算法，本文突出真实推理系统开销。
- [[LoRA-Flow词元级动态低秩融合]] 同样按生成词元改变融合权重，但未解决相同系统问题。

## 疑问与待验证

- 三物理专家在 RTX 5090 上的端到端延迟是否显著高于同总秩单适配器？

## 原始摘要

> 摘要要点经全文第 1 页核验：论文分析动态适配器的内核启动开销，并通过词元级预路由和内核融合降低解码延迟。此处为中文转述。

## 文献信息

- arXiv：[2405.17741](https://arxiv.org/abs/2405.17741)
- OpenReview：[NIG8O2zQSQ](https://openreview.net/forum?id=NIG8O2zQSQ)
- DBLP：[CoRR abs/2405.17741](https://dblp.org/rec/journals/corr/abs-2405-17741)
