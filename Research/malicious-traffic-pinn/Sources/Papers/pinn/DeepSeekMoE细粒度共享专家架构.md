---
title: "DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models"
authors:
  - Damai Dai
  - Chengqi Deng
  - Chenggang Zhao
  - R.X. Xu
  - Huazuo Gao
  - Deli Chen
  - Jiashi Li
  - Wangding Zeng
  - Xingkai Yu
  - Y. Wu
  - Zhenda Xie
  - Y.K. Li
  - Panpan Huang
  - Fuli Luo
  - Chong Ruan
  - Zhifang Sui
  - Wenfeng Liang
year: 2024
date: 2026-07-22
journal: "Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics"
source_pdf: "[[raw/papers/pinn/2024-Dai-DeepSeekMoE.pdf]]"
tags:
  - 类型/论文
  - 主题/混合专家
  - 主题/共享专家
  - 主题/专家专门化
key_finding: "DeepSeekMoE 以细粒度专家划分和始终激活的共享专家压缩共性知识，但其路由专家的专门化来自大规模语言建模，并不等于可解释的物理状态专门化。"
method: "细粒度专家分割、共享专家隔离、词元级稀疏路由"
baseline: "GShard、密集模型、LLaMA2 7B、DeepSeek 7B"
aliases:
  - DeepSeekMoE
  - Dai2024-DeepSeekMoE
---

# DeepSeekMoE 细粒度共享专家架构

> Damai Dai 等，2024，ACL 长文 · 本地 PDF 33 页

## 一句话

论文支持“共性能力由共享专家承担、差异能力由路由专家承担”的结构先例，但不能证明自由路由会自然形成平稳传输、队列累积或容量饱和等物理语义。

## 背景

普通混合专家将每个词元分配给少数完整前馈专家。专家粒度较粗时，一个专家容易同时承载多种知识；多个专家也可能重复学习共性知识。论文把问题定义为专家专门化不足，而不是多任务损失权重冲突。

## 方法核心

标准稀疏专家层可写为

$$
h_t=\sum_{i=1}^{N}g_{i,t}\operatorname{FFN}_i(u_t)+u_t,
$$

其中每个词元只有 Top-K 个 $g_{i,t}$ 非零。DeepSeekMoE 做两项改变：

- 将 $N$ 个粗专家细分为 $mN$ 个较小专家，同时激活 $mK$ 个，使同一计算预算下的专家组合更灵活。
- 单独设置始终激活的共享专家，用于吸收跨上下文共性知识，减少路由专家重复。

共享专家和路由专家都位于语言模型前馈层。论文没有固定人类可解释的专家标签，也没有按物理控制体状态监督路由。

## 实验结果

- DeepSeekMoE 2B 在 12 个语言基准上显著优于同规模 GShard 2B，并接近专家参数和计算量约为其 1.5 倍的 GShard 2.9B。
- DeepSeekMoE 16B 在约 40% 计算量下取得与 DeepSeek 7B、LLaMA2 7B 相近的综合性能。
- 论文通过消融和专家激活分析支持细粒度分割与共享专家隔离，但这些分析展示的是语言知识分布，不是物理量可辨识性。

## 我的理解

对当前课题，最有价值的是“共享共性、隔离差异”的结构逻辑。当前 S3 家族检测应被视为已验证的共享检测能力，物理私有适配器只服务子类与开放集。不同之处在于，本课题需要显式任务门控和冻结条件，而不是让学习型路由决定家族任务是否使用物理分支。

若以后验证物理状态路由适配专家，DeepSeekMoE 只能支持“共享专家 + 路由专家”的结构来源。专家语义必须由队列状态监督、路由统计和反事实扰动另行验证。

## 局限与不可外推结论

- 论文研究从头预训练的 2B 至 145B 混合专家模型，不是 1.7B 基座上的 LoRA 修复。
- 词元级 Top-K 路由可能受到文本表面模式影响，不能保证按网络动力学分工。
- “共享专家隔离”不等于严格分支不变性；只要家族路径仍经过可训练路由或私有专家，原输出就可能变化。
- 论文不能证明多专家结构优于同参数预算的单物理适配器。

## 与相关工作的关系

- 与 [[MixLoRA词元级低秩专家混合]] 的共同点是词元级稀疏路由；区别是 DeepSeekMoE 从头训练完整前馈专家。
- 与 [[MoDULA通用与领域专用低秩适配]] 的共同点是共性与专用参数分离；MoDULA 更接近低秩适配场景。
- 与 [[物理硬约束混合专家]] 的“专家”含义不同，后者按物理域分块求解硬约束。

## 疑问与待验证

- 序列级物理路由能否比词元级路由更稳定，并避免把提示词格式当作专家选择捷径？
- 在同总秩和同激活参数预算下，三物理专家是否优于一个物理私有适配器？

## 原始摘要

> 摘要要点经本地全文第 1 页和 ACL 正式页面核验：论文通过细粒度专家分割和共享专家隔离提高专家专门化，并在 2B、16B 及更大规模验证计算效率。此处为中文转述。

## 文献信息

- DOI：[10.18653/v1/2024.acl-long.70](https://doi.org/10.18653/v1/2024.acl-long.70)
- ACL Anthology：[2024.acl-long.70](https://aclanthology.org/2024.acl-long.70/)
- arXiv：[2401.06066](https://arxiv.org/abs/2401.06066)
