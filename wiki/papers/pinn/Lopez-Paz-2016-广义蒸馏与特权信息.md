---
title: "Unifying Distillation and Privileged Information"
authors:
  - David Lopez-Paz
  - Léon Bottou
  - Bernhard Schölkopf
  - Vladimir Vapnik
year: 2016
date: 2026-08-05
journal: "International Conference on Learning Representations"
source_pdf: "[[raw/papers/pinn/Lopez-Paz-2016-广义蒸馏与特权信息.pdf]]"
tags:
  - 特权信息学习
  - 知识蒸馏
  - PINN
  - 类型/论文
key_finding: "广义蒸馏允许教师在训练时使用推理不可得的特权表示，通过软目标把知识转移给只使用常规输入的学生。"
method: "特权教师软标签与硬标签联合的广义蒸馏"
baseline: "普通监督、标准蒸馏、SVM+ 与特权信息知识转移"
aliases:
  - Lopez-Paz2016-广义蒸馏
---

# 广义蒸馏与特权信息

## 一句话

训练期的额外信息可以先教会教师，再通过软预测与硬标签联合监督转移给推理时只见常规输入的学生。

## 方法核心

设常规输入为 $x_i$，仅训练可得的特权信息为 $x_i^*$，标签为 $y_i$。教师用 $(x_i^*,y_i)$ 训练并产生温度软化预测 $s_i$，学生用 $x_i$ 同时学习硬标签与 $s_i$。蒸馏目标在模仿教师与拟合真实标签之间使用系数 $\lambda$ 取舍。算法步骤与公式见 PDF 第 3–4 页。

## 论文原结论

- 特权信息在测试时不可得，学生的最终决策必须只依赖 $x$，见 PDF 第 1 页。
- 广义蒸馏先学教师、再生成软目标、最后学学生，见 PDF 第 4 页。
- 理论受教师和学生函数类复杂度、样本量和特权表示质量限制，不能推导为任意额外信息必然提升。

## 本课题推论

- ns-3 发送者级 TCP 状态和方程上下文可作为训练期特权信息。
- 网络级学生只接收公开数据可构造的窗口历史，避免在推理时要求不可观测的发送者身份。
- 论文没有证明这一迁移在恶意流量检测中必然成功，必须用置换和随机特权信息对照验证。

## 文献信息

- arXiv：[1511.03643](https://arxiv.org/abs/1511.03643)
- 发表：ICLR 2016

