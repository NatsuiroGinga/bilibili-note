---
title: "Augmented Physics-Informed Neural Networks: A Gating Network-Based Soft Domain Decomposition Methodology"
authors:
  - Zheyuan Hu
  - Ameya D. Jagtap
  - George Em Karniadakis
  - Kenji Kawaguchi
year: 2023
date: 2026-07-22
journal: "arXiv preprint"
source_pdf: "[[raw/papers/pinn/2022-Hu-APINN.pdf]]"
tags:
  - 类型/论文
  - 主题/物理信息神经网络
  - 主题/软域分解
  - 主题/门控网络
key_finding: "APINN 用可训练门控对物理域做软分解，并让子网部分共享参数；性能强烈依赖门控初始化，说明学习型物理路由必须有物理先验而不能任意初始化。"
method: "软域分解、分区统一门控、子网部分参数共享、PINN 泛化界"
baseline: "PINN、XPINN、固定门控 APINN"
aliases:
  - APINN
  - Hu2023-APINN
---

# APINN 门控软域分解

> Zheyuan Hu 等，2023，arXiv 第 3 版 · PDF 27 页

## 一句话

APINN 是“门控 + 部分共享 + 物理子网”的直接先例，但它按连续时空域分解偏微分方程解，不能直接证明网络流量序列的低秩专家路由有效。

## 背景

XPINN 把时空域硬切成多个子域，每个子网只看本子域数据，并依赖界面连续性损失。硬切分可能导致子域数据过少和界面误差。APINN 用分区统一的软门控加权所有子网输出，让每个子网都可利用全域样本。

## 方法核心

若 $G_i(x)$ 是非负且和为 1 的门控，$u_i(x)$ 是子网，则 APINN 输出可概括为

$$
\hat u(x)=\sum_i G_i(x)u_i(x),\qquad \sum_iG_i(x)=1.
$$

子网前部共享参数、后部保持专用。论文分别分析固定和可训练门控的泛化界，核心权衡是：分解后目标函数更简单，但子模型与门控的复杂度会增加。

## 实验结果

- Burgers 方程 10 次独立运行中，PINN 相对 $L_2$ 误差为 $1.620\times10^{-3}$，最佳 APINN-X 为 $9.109\times10^{-4}$；XPINN 两个变体约为 $1.49\times10^{-1}$ 与 $1.304\times10^{-1}$。
- Helmholtz 方程中，PINN 为 $2.438\times10^{-3}$，APINN-X 为 $1.275\times10^{-3}$，XPINN 的正则化变体为 $1.297\times10^{-3}$。
- 不同门控初始化可产生显著不同结果；在 Burgers 任务中，MPINN 式初始化比 XPINN 式初始化差，训练后的门控仍明显受初始化影响。

## 我的理解

APINN 对备选物理专家路线的关键启示不是“使用自由门控”，而是“路由必须从有意义的物理分区开始”。当前可定义的三个序列级状态是平稳传输、队列累积、容量饱和，并应由队列状态或残差监督验证。

当前唯一修复只使用一个私有物理适配器，不需要 APINN 门控。只有单适配器失败且用户批准后，APINN 才能作为多专家备选的物理路由来源。

## 局限与不可外推结论

- 理论建立在偏微分方程函数逼近和特定复杂度界上，不能直接成为 Transformer 检测误差界。
- 软门控改善不稳定，初始化可能决定最终分解。
- 子网都参与加权输出，不提供家族分支严格不变性。
- 论文不涉及仿真到公开流量数据的域偏移。

## 与相关工作的关系

- [[物理硬约束混合专家]] 使用固定物理域分块和可微硬约束，路由含义更确定。
- [[StableMoE稳定路由策略]] 从语言模型角度说明动态路由在训练中也会波动。

## 疑问与待验证

- 公共五字段是否足以稳定区分三种队列状态，而不泄漏 ns-3 场景编号？

## 原始摘要

> 摘要要点经全文第 1 页核验：论文以可训练软门控、全域样本和部分参数共享改进 PINN/XPINN，并分析门控初始化与泛化。此处为中文转述。

## 文献信息

- arXiv：[2211.08939](https://arxiv.org/abs/2211.08939)
- 发表状态：本次仅核验到 arXiv 第 3 版。
