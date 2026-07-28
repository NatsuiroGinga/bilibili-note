---
title: "Auxiliary-Tasks Learning for Physics-Informed Neural Network-Based Partial Differential Equations Solving"
authors:
  - Junjun Yan
  - Xinhai Chen
  - Zhichao Wang
  - Enqiang Zhou
  - Jie Liu
year: 2023
date: 2026-07-22
journal: "arXiv preprint"
source_pdf: "[[raw/papers/pinn/2023-Yan-辅助任务PINN.pdf]]"
tags:
  - 类型/论文
  - 主题/物理信息神经网络
  - 主题/辅助任务学习
  - 主题/共享私有结构
key_finding: "ATL-PINN 比较硬共享、软共享、MMoE 和 PLE 四种物理辅助任务结构，并用梯度余弦筛选辅助更新，直接说明 PINN 多任务可通过共享私有结构减轻跷跷板效应。"
method: "Hard-ATL、Soft-ATL、MMoE-ATL、PLE-ATL、梯度余弦筛选"
baseline: "单任务 PINN、四类辅助任务结构及其梯度策略"
aliases:
  - ATL-PINN
  - Yan2023-ATLPINN
---

# 辅助任务 PINN 共享私有与专家结构

> Junjun Yan 等，2023，arXiv · PDF 16 页

## 一句话

该论文是 PINN 与共享私有多任务结构的直接桥梁，但其正梯度筛选和 PDE 辅助任务不能推翻本课题已经完成的博弈与软协调负结论。

## 方法核心

论文比较四类结构：共享特征后分任务塔的硬共享；共享与任务专用专家并存的软共享；每任务独立门控共享专家的 MMoE；同时具有共享与任务专用专家的 PLE。PLE 用私有和公共参数减轻任务关系较弱时的跷跷板效应。

对共享参数，论文计算

$$
\cos(\nabla L_{main},\nabla L_{aux})=
\frac{\nabla L_{main}\cdot\nabla L_{aux}}
{\|\nabla L_{main}\|\,\|\nabla L_{aux}\|},
$$

只在余弦为正时合并辅助梯度。

## 实验结果

三类 PDEBench 问题中，作者报告相对单任务 PINN 的最大精度改善 96.62%，平均改善 28.23%。不同共享结构并非在所有方程上同样最优，任务关系与网络结构会改变结果。

## 我的理解

该论文支持“PINN 信号不一定要写入全部共享参数，私有专家可缓解负迁移”。当前实验已有 20/20 负余弦与 S3/S4 相反收益，因此冻结 S3 并把物理梯度限定到私有 LoRA，比再做余弦筛选更符合现有证据。

双锚点监督和有限队列残差应训练新状态头与物理私有 LoRA；家族任务固定 $g_F=0$。未知攻击标签不进入训练或校准。

## 局限与不可外推结论

- 论文是相同 PDE 不同初边值条件的辅助任务，相关性强于公开流量与 ns-3 的关系。
- 梯度余弦筛选仍是软优化策略，本课题已有相关失败证据。
- 预印本没有正式会议或期刊状态；大幅百分比不能外推到检测 F1。

## 与相关工作的关系

- [[APINN门控软域分解]] 从空间域分解构造物理子网。
- [[对抗式多任务文本分类共享私有表征]] 提供私有表示进入任务输出的非物理先例。
- [[Recon从结构根源减少梯度冲突]] 支持在高冲突位置做结构隔离。

## 原始摘要

> 摘要要点经全文第 1 页核验：论文将四种辅助任务结构和梯度余弦策略用于 PINN，并在三个 PDE 问题验证。此处为中文转述。

## 文献信息

- arXiv：[2307.06167](https://arxiv.org/abs/2307.06167)
- 发表状态：本次核验为 CoRR/arXiv 非正式出版物。
