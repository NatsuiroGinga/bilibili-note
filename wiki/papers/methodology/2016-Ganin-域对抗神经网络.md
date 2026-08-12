---
title: "域对抗神经网络训练"
authors: [Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, François Laviolette, Mario Marchand, Victor Lempitsky]
year: 2016
date: 2026-08-11
journal: "Journal of Machine Learning Research"
source_pdf: "[[raw/papers/methodology/2016-Ganin-Domain-Adversarial-Training.pdf]]"
tags: [无监督域适配, 域对抗, 梯度反转, 类型/论文]
key_finding: "通过梯度反转同时降低源任务损失并混淆源/目标域分类器，学习域不变表示；边缘对齐不保证条件对齐。"
---

# 域对抗神经网络训练

## 全文核验结论

DANN 使用有标签源域和无标签目标域，特征提取器一方面服务任务分类，另一方面经梯度反转最大化域分类损失。证据位于 PDF 第1至4页及第10至13页算法。

## LSPR 角色

它可合法使用 LSPR24 无标签前缀，是 OT 的域对齐强基线，也可测试“移除年度信息”是否有益。可观测量包括域分类准确率、源任务损失、目标平均精确率和少数攻击分数分离度。

## 最小证伪与边界

若域分类准确率下降但目标平均精确率同时下降，说明边缘对齐抹除了攻击相关结构，应停止。不能把域不可辨识解释为因果不变，也不能忽略目标前缀攻击污染。

## 证据记录

- 全文状态：完成逐项核验。
- Zotero：`7GR6INSP`。
- 课题角色：备选路线三与环境对抗的强基线。
