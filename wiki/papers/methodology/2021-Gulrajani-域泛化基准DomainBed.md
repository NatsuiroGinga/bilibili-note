---
title: "In Search of Lost Domain Generalization（DomainBed 基准）"
authors: [Ishaan Gulrajani, David Lopez-Paz]
year: 2021
date: 2026-10-15
journal: "ICLR 2021（arXiv 2007.01434）"
source_pdf: "[[raw/papers/methodology/2021-Gulrajani-LopezPaz-In-Search-of-Lost-Domain-Generalization.pdf]]"
tags: [域泛化, 基准协议, 经验风险最小化, 模型选择, 类型/论文]
key_finding: "在统一协议（7 数据集/9 基线/3 模型选择准则）下，精心实现的 ERM 在全部数据集上追平或超过专用域泛化方法；并主张「模型选择方法是算法的一部分」，算法不声明模型选择方法即为不完整。"
---

# In Search of Lost Domain Generalization（DomainBed 基准）

## 全文核验结论

- 作者质疑「域泛化算法已经优于 ERM」的既有印象，指出实验条件（数据集、架构、模型选择准则）不一致使比较不公平（摘要，物理第 1 页）。
- 发布 **DomainBed**：7 个多域数据集、9 个基线算法、3 种模型选择准则（摘要，第 1 页）。
- 核心结论（原文）：*"when carefully implemented, empirical risk minimization shows state-of-the-art performance across all datasets"*（摘要，第 1 页；Table 1，第 2 页）。
- Table 1（第 2 页）实测：ERM 超过文献报告值——
  - RotatedMNIST 平均 `98.0` vs 前人 `97.2`；
  - PACS 平均 `85.7` vs 前人 `84.5`；
  - VLCS 平均 `77.4` vs 前人 `75.9`；
  - Office-Home 平均 `67.5` vs 前人 `65.5`。
- 两条 Recommendation（第 4 页）：
  - **Recommendation 1**：域泛化算法有责任声明其模型选择方法，不声明即为不完整。
  - **Recommendation 2**：使用 oracle（测试域）选择的结果必须显式披露，并限制访问测试域的查询次数（本文设每个算法 20 次）。
- 三种模型选择准则（§3.1，第 4 页）：训练域验证集、留一域交叉验证（leave-one-domain-out）、测试域验证集（oracle）。

## 对本课题（LAMDA 年度漂移、第四章 group 级最坏风险）的合法映射

- 这是「group-DRO 家族赌注」的**直接威胁文献**：它表明在既有基准上，按域（组）构造的不变性/最坏组目标并不自动优于按经验风险平均训练的 ERM。
- 对本课题的含义不是「放弃 group 目标」，而是：**(a) 必须以 ERM（本数据、同预算）为强基线**；**(b) 必须把「按年份分组 + 最坏年风险」的增益证明为在共同预算下相对 ERM 的净增益**；**(c) 模型选择方法必须显式声明并计入算法**——年度序列下不能悄悄用目标年份选超参。

## 原创边界与不能直接声称

- 本文实验域为视觉多域基准（RotatedMNIST/PACS/VLCS/Office-Home 等），**不涉及**恶意软件或年度时间序。不能据本文断言「group-DRO 在 Android 年度漂移上一定无效」；只能断言「该家族在既有基准上对 ERM 的增益需独立证明」。
- Wang et al. 2024（AAAI）给出理论解释（训练域数量不足），见 `[[2024-Wang-丢失域泛化源于训练域不足]]`；本课题年度序列最多十余年、域数远少于 Ω(1/ε²)，是否落入该解释范围需自行核验，不直接引用。

## 证据记录

- 全文状态：已下载并逐页核验（摘要、Table 1、Recommendation、§3.1）。
- 稳定标识：arXiv `2007.01434`（v1 2020-07-02）；ICLR 2021。
- Zotero：未单独入库（以 raw 原件 + 本笔记为准）。
- 课题角色：第四章「group 目标是否值得押注」的负面证据基线；ERM 强基线的协议来源。
