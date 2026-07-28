---
title: "StableMoE: Stable Routing Strategy for Mixture of Experts"
authors:
  - Damai Dai
  - Li Dong
  - Shuming Ma
  - Bo Zheng
  - Zhifang Sui
  - Baobao Chang
  - Furu Wei
year: 2022
date: 2026-07-22
journal: "Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics"
source_pdf: "[[raw/papers/pinn/2022-Dai-StableMoE.pdf]]"
tags:
  - 类型/论文
  - 主题/混合专家
  - 主题/路由稳定性
key_finding: "StableMoE 发现同一样本在训练中会不断更换专家，并用先学习、再蒸馏冻结路由的两阶段方案提高样本效率；冻结也会牺牲后续适应性。"
method: "平衡且凝聚的路由、轻量路由蒸馏、第二阶段冻结"
baseline: "Switch、BASE、动态学习路由"
aliases:
  - StableMoE
  - Dai2022-StableMoE
---

# StableMoE 稳定路由策略

> Damai Dai 等，2022，ACL 长文 · PDF 11 页

## 一句话

论文直接证明自由学习路由会波动，因此物理专家若存在，应使用物理先验和冻结的序列级路由，而不是在 202 步小样本训练中持续漂移。

## 方法核心

第一阶段联合学习平衡且凝聚的动态路由，并蒸馏为脱离主干的轻量路由器；第二阶段用蒸馏路由固定词元到专家的指派。固定路由避免同一样本在多个专家间反复写入，提升样本效率。

## 实验结果

论文在基线中观察到 40.9% 的词元在训练完成 20% 后仍会换专家，29.1% 在过半后仍变化，15.4% 在 80% 训练后仍变化。语言建模和多语言翻译实验显示 StableMoE 在收敛速度与最终性能上优于所比较路由方法。

## 我的理解

当前候选物理专家只有在单私有修复失败后才可能启用。若启用，先用 ns-3 物理状态定义路由，再冻结路由用于公开数据，比完全自由 Top-K 更符合可解释性和小样本条件。

## 局限与不可外推结论

- 冻结过早会锁定错误路由，降低适应新域的能力。
- 词元级语言路由结果不能证明序列级队列状态路由有效。
- 论文没有同参数单 LoRA 对照或家族分支不变性。

## 原始摘要

> 摘要要点经全文第 1 页和 ACL Anthology 页面核验：论文以两阶段路由蒸馏和冻结解决训练中的路由波动。此处为中文转述。

## 文献信息

- DOI：[10.18653/v1/2022.acl-long.489](https://doi.org/10.18653/v1/2022.acl-long.489)
- ACL Anthology：[2022.acl-long.489](https://aclanthology.org/2022.acl-long.489/)
