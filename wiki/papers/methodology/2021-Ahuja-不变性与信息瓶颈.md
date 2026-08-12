---
title: "不变性原理与信息瓶颈的分布外泛化"
authors: [Kartik Ahuja, Ethan Caballero, Dinghuai Zhang, Jean-Christophe Gagnon-Audet, Yoshua Bengio, Ioannis Mitliagkas, Irina Rish]
year: 2021
date: 2026-08-11
journal: "NeurIPS 2021"
source_pdf: "[[raw/papers/methodology/2021-Ahuja-Invariance-Information-Bottleneck.pdf]]"
tags: [不变学习, 信息瓶颈, 分布外泛化, 类型/论文]
key_finding: "说明仅靠不变性在一般分类分布外问题中不足，并在附加结构假设下把信息瓶颈与不变性结合。"
---

# 不变性原理与信息瓶颈的分布外泛化

## 全文核验结论

论文先给出一般分类分布外泛化的不可能性与反例，再在结构条件下研究信息瓶颈和不变性组合。核心提醒是：源环境上的预测不变不能唯一识别真正可迁移特征。证据位于 PDF 第1至4页和理论部分。

## LSPR 角色

可把 RWKV 状态压缩与环境不变项作为对照，但必须监控攻击信息是否一并被删去。可观测量为状态对环境的可预测性、状态对标签的可预测性、互信息代理和目标平均精确率。

## 最小证伪与边界

比较无瓶颈、仅瓶颈、仅环境项与二者组合。若环境信息下降但攻击类别间隔和跨年排序也下降，即否决。不能从本文推断有限 LSPR 时间环境满足其可识别条件。

## 证据记录

- 全文状态：完成逐项核验。
- Zotero：`N6A4V732`。
- 课题角色：环境不变路线的理论警戒与基线。
