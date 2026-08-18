---
title: "Stochastic Optimization of Areas Under Precision-Recall Curves with Provable Convergence"
authors: [Qi Qi, Youzhi Luo, Zhao Xu, Shuiwang Ji, Tianbao Yang]
year: 2021
date: 2026-08-13
journal: "Advances in Neural Information Processing Systems 34（NeurIPS 2021），1752–1765"
source_pdf: "[[raw/papers/methodology/ranking/2021-Qi-SOAP-AUPRC-NeurIPS.pdf]]"
sha256: "99fbcb99c4b0a052f14f56bb6f3e845548ed1440a59c76d7d05d513a8e3c8ec2"
tags:
  - 平均精确率
  - 随机复合优化
  - 类别不平衡
  - 类型/论文
key_finding: "把经验 AP 写成正样本外层有限和与全样本内层期望的耦合复合目标，并用逐正样本移动状态构造 SOAP；算法 1 明确把瞬时随机梯度估计称为有偏估计，论文证明的是其误差受控后的收敛而非逐步无偏。"
method: "SOAP 维护每个正样本的两个内层统计量，以移动平均更新分子和分母，再用随机正锚点与随机比较样本更新模型。"
baseline: "交叉熵、类别平衡交叉熵、焦点损失、LDAM、AUROC 最大化、Smooth-AP、FastAP 等"
aliases:
  - SOAP
  - Qi2021-SOAP
---

# SOAP：直接优化 AUPRC 的耦合复合随机方法

> Qi 等，2021，NeurIPS · 14 个物理页 · Zotero `MHNH9QBM`

## 论文原结论

- 第 3 页公式（1）给出经验 AP；公式（2）—（4）把它改写成以正样本为外层索引、以全数据为内层比较集的复合目标。
- 第 4 页引入逐正样本的移动状态 `u`，分别跟踪 AP 比率中的两个内层量。
- 第 5 页算法 1 的第 7 步明确标注为“有偏随机梯度估计”。因此，不能把 SOAP 的收敛保证改写成每一步梯度严格无偏。
- 第 5 页假设 1要求损失有正下界、有界、光滑、利普希茨且随机内层函数及其梯度方差有界；第 6 页定理 1—2在这些条件和特定步长下给出收敛率。

## 与本课题的关系

- **可迁移机制**：实体分数可替代样本分数进入 AP 的外层正锚点／内层比较结构；SOAP 是直接实体 AP 代理的核心前作。
- **本课题推论**：即使实体内 `p` 阶矩估计无偏，把它代入 SOAP 的比率型外层后，整条随机梯度一般仍有偏；必须沿用状态跟踪或另证偏差控制。
- **不可直接声称**：首次直接优化 AP、首次提出 AP 随机优化器、或“使用 SOAP 就得到无偏梯度”。
- **实验待证**：SOAP 的假设、状态数量和极少正实体下的方差是否适用于 LSPR23→LSPR24 实体任务。

## 证据记录

- 全文：会议正式 PDF，14 页；关键位置为物理第 3—6 页。
- 官方页：<https://proceedings.neurips.cc/paper/2021/hash/0dd1bc593a91620daecf7723d2235624-Abstract.html>
- 证据强度：支持直接 AP 与有偏但受控的随机复合优化；不支持本项目方法有效。

