---
title: "Impossibility Theorems for Domain Adaptation"
authors:
  - Shai Ben-David
  - Teresa Luu
  - Tyler Lu
  - Dávid Pál
year: 2010
date: 2026-08-19
journal: "Proceedings of the 13th International Conference on Artificial Intelligence and Statistics (AISTATS) 2010, Chia Laguna Resort, Sardinia, Italy. JMLR Workshop and Conference Proceedings, Volume 9"
source_pdf: "[[raw/papers/methodology/2010-Ben-David-Impossibility-Theorems-Domain-Adaptation.pdf]]"
tags:
  - 域适应
  - 理论界
  - 协变量移位
  - 不可能性
  - 类型/论文
key_finding: "证明在只有源域标签与目标域无标签样本时，仅靠「无标签分布相似 + 协变量移位」或「存在双域低误差假设 + 协变量移位」都不足以保证域适应成功；负结果对**任何不能访问目标域标注样本的域适应算法**成立（原件 p.1 摘要）。"
aliases:
  - Ben-David2010-Impossibility
related:
  - "[[2016-Ganin-DANN域对抗训练]]"
  - "[[2019-Azizzadenesheli-RLLS标签移位正则化学习]]"
---

# 域适应的不可能性定理

## 一句话

给域适应划出理论下界：没有目标域标签，常被援引的三条假设无论怎么组合都不够，协变量移位这一条尤其弱。

## 题录与原件（全文核验）

- 原件：`raw/papers/methodology/2010-Ben-David-Impossibility-Theorems-Domain-Adaptation.pdf`，8 页。
- 题录逐项从原件 p.1 页脚核出：`Appearing in Proceedings of the 13th International Conference on
  Artificial Intelligence and Statistics (AISTATS) 2010, Chia Laguna Resort, Sardinia, Italy.
  Volume 9 of JMLR: W&CP 9. Copyright 2010 by the authors.` **卷号原件可读；卷内页码原件未印。**
- 证据等级：**同行评议正式发表**（AISTATS）。
- 本笔记补建缘由：该原件此前无 `wiki/papers/` 笔记（2026-08-19 轴二文献盘点发现）。

## 论文原结论（页级证据）

- p.1 摘要：在 agnostic PAC 风格的学习模型下研究三条假设——
  (i) 两个无标签分布之间的相似性；(ii) 假设类中存在在源与目标上都低误差的分类器；
  (iii) 协变量移位假设，即每个数据点的条件标签分布在源与目标上相同。
  **结论：缺了 (i) 或 (ii) 中任一条，其余假设的组合都不足以保证学习成功。**
- p.1 摘要原句（本课题最关键的一句）：
  `Our negative results hold with respect to any domain adaptation learning algorithm,
  as long as it does not have access to target labeled examples.`
- p.1 摘要续：并给出形式化证明，说明「广受欢迎的协变量移位假设相当弱，
  并不能免除其他假设的必要性」。
- p.2（正文）：协变量移位「不能保证 DA 成功，除非域中的点被访问多次」。
- p.2：既不是「协变量移位 + 无标签分布间 dA 小」，也不是「协变量移位 + 存在低误差假设」这一对，
  在只能从目标分布取无标签样本时足够。**在不做进一步假设时两条都是必需的。**
- p.3：现有 DA 性能保证多针对「保守型」算法，即忽略可用的目标域无标签数据的算法。

## 本课题推论（非论文原结论）

- 这条定理给 1.2.2 段二的共同短板提供了**理论层面**的支撑，而不只是经验层面：
  适应类方法之所以都要求目标域数据，不是工程惯例而是理论必要性。
- 由此可以论证本课题的选择：既然在零目标数据条件下无法通过「适应」获得保证，
  就只能改变模型在源域内学到的**结构**——即表示层的跨流上下文与决策层的实体级聚合，
  使其对年度间的变化天然更不敏感。**该论证是本课题推论，不是论文原结论，须在正文中区分。**

## 不可直接声称的内容

- 不得写成「Ben-David 等证明域适应不可能」。定理是条件性的：
  证明的是**特定假设组合下的不充分性**，不是域适应整体不可行。
- 不得据它否定 DANN、BBSE、RLLS 等方法本身；这些方法在其假设成立时有效。

## 与本课题的关系

- 落 1.2.2 段二，是段末共同短板的**理论出处**（其余为经验出处）。
