---
title: "Learning Using Privileged Information: Similarity Control and Knowledge Transfer"
authors:
  - Vladimir Vapnik
  - Rauf Izmailov
year: 2015
date: 2026-08-05
journal: "Journal of Machine Learning Research"
source_pdf: "[[raw/papers/pinn/Vapnik-Izmailov-2015-特权信息学习与知识迁移.pdf]]"
tags:
  - 特权信息学习
  - 教师学生
  - PINN
  - 类型/论文
key_finding: "特权信息只在训练阶段出现，可通过相似性修正或教师到学生的知识迁移改善只使用常规输入的学生。"
method: "相似性控制与教师学生知识迁移"
baseline: "传统学习与 SVM+"
aliases:
  - Vapnik2015-LUPI
---

# 特权信息学习与知识迁移

## 一句话

学生推理时不需要教师信息，教师的作用是在训练时传递样本难度、相似性或可迁移表示。

## 方法核心

论文区分两种机制：教师用特权表示修正学生对样本相似性或难度的理解；教师先在特权空间学到知识表示，再将可迁移部分交给只使用普通输入的学生。训练与测试信息非对称的定义见 PDF 第 2–3 页。

## 论文原结论

- 特权信息只在训练期提供，测试阶段学生独立运行，见 PDF 第 2 页。
- 论文给出相似性控制和直接知识迁移两条路径，不要求将特权原始字段带入部署。

## 本课题推论

- 发送者级真值可以留在教师空间，不必强迫网络级学生逐发送者恢复。
- 不能把这篇论文当作检测性能不降的保证；性能保护必须由冻结锚点和可回退门控实现。

## 文献信息

- JMLR：[Volume 16, Paper 61](https://www.jmlr.org/papers/v16/vapnik15b.html)

