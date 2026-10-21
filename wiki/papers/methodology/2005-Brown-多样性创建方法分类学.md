---
title: "Diversity creation methods: a survey and categorisation"
authors: [Gavin Brown, Jeremy Wyatt, Rachel Harris, Xin Yao]
year: 2005
date: 2026-10-21
journal: "Information Fusion 6(1):5–20，DOI 10.1016/j.inffus.2004.04.004（题名核验：正题为 a survey and categorisation，此前登记的 old and new 有误）"
source_pdf: "[[raw/papers/methodology/2005-Brown-DiversityCreationMethods-Survey.pdf]]"
sha256: "0fc1dbf3a238c929ae7fe82350b0db7440cb36aef5838c05c65dc9eaa5b54b6b"
arxiv_id: ""
zotero_item_key: ""
bibtex_key: "brown_diversity_2005"
tags:
  - 集成学习
  - 多样性
  - 分类学
  - 负相关学习
  - 类型/论文
key_finding: "歧义分解给出保证：凸组合误差 ≤ 成员平均误差（歧义项恒正、做减法），但『多样性本身并不足够』——歧义项（多样性）与个体平均误差（精度）必须取平衡才能最低集成误差（§2.1.1）。多样性创建方法分隐式（Bagging：纯随机、不测多样性）与显式（Boosting：直接操纵训练分布）两类（§3），另给出应用的三个维度。"
method: "综述与分类学：系统整理分类任务下的多样性创建技术，提出 implicit/explicit 二分与三个应用维度；§2.1 显式给出 bias–variance–covariance 分解与歧义分解的互推"
baseline: "—（综述，无统一实验基线；各节引用对应原文献的实证）"
aliases:
  - Brown2005-Diversity
  - 多样性创建方法综述
related:
  - "[[1995-Krogh-神经网络集成歧义分解]]"
  - "[[1999-Liu-负相关学习NCL]]"
---

# 多样性创建方法：综述与分类学

> Brown、Wyatt、Harris、Yao，*Information Fusion* 6(1):5–20，2005。用户 2026-10-21 手动下载（Elsevier 付费墙，代理通道不可达）。

## 一句话

把「集成成员要多样」从经验口号整理成分类学：歧义分解保证凸组合不劣于平均成员（但精度与多样性要平衡），多样性创建方法按是否在构建中显式度量多样性分为 implicit（Bagging 类，靠随机）与 explicit（Boosting/NCL 类，直接操纵）。

## 题录与原件

- 题名核验：PDF 第 1 页原题为 **"Diversity creation methods: a survey and categorisation"**；作者、单位（Birmingham）、收稿/录用日期见第 1 页。**此前任务登记的副题 "old and new" 有误，以本页为准**。
- 原件：`raw/papers/methodology/2005-Brown-DiversityCreationMethods-Survey.pdf`；SHA-256 见 frontmatter。
- DOI：`10.1016/j.inffus.2004.04.004`。

## 与本课题骨架的接口（页码锚点）

1. **§2.1.1（歧义分解的精确表述与边界）**：$E_{ens}=\sum_i w_i(f_i-d)^2-\sum_i \bar w_i (f_i-f_{ens})^2$——第一项是加权平均成员误差，第二项（歧义）恒正做减法，故集成误差有保证地不高于平均成员误差；**但原文同时警告「多样性本身并不足够」：个体误差随多样性上升，须在两者间取平衡**。这是本课题机制二（反合流＝抬 Ā）的主张边界：NCL 臂若只抬分歧而伤个体精度（Ē），增益会被第一项吃掉——机制核查项「2024 不一致率上升」必须与「F1 判据」同时成立才有意义。
2. **§3 分类学**：implicit（Bagging：随机采样制造分歧，全程不测多样性）vs explicit（Boosting：直接操纵训练分布）。**TabM 的随机符号首适配属 implicit（初始化随机性），本课题机制二的 NCL 惩罚属 explicit**——两者在分类学上的位置不同、作用面互补，这为「机制一获得 Ā、机制二维持 Ā」的分工提供了分类学注脚。
3. **§2.1（BVC 与歧义分解互推）**：原文显式证明两个分解的等价性，支持本课题把「方差缩减命题」（命题 1）与「歧义分解」当同一账本的两面引用。

## 不能支持的论断

- 本文是分类任务的综述与分类学，**不提供分类任务下多样性的完备形式化**（原文自认「understanding of classifier error diversity is still incomplete」，第 1–2 页）；
- 本文不含年度漂移、持续学习或恶意流量内容，不支持任何漂移相关结论；
- 「显式优于隐式」不是本文结论——原文对两类方法只作区分，优劣由具体任务实证决定。

## 证据等级

- 原件级别：Elsevier 正式出版物全文（18 页），§2.1.1 与 §3 已对照 MinerU 转换文本核验（转换件 `/tmp/brown-extract/`，不入库）。
- 可支撑：歧义分解的保证与平衡条件、implicit/explicit 分类学、BVC–歧义互推。
- 实验待证：本课题机制二（反合流）在 LAMDA 协议下的实际增益（先导运行中）。
