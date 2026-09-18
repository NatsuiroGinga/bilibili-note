---
title: "Label Delay in Online Continual Learning"
authors: [Botos Csaba, Wenxuan Zhang, Matthias Müller, Ser-Nam Lim, Mohamed Elhoseiny, Philip Torr, Adel Bibi]
year: 2024
date: 2026-09-09
journal: "NeurIPS 2024；arXiv:2312.00923v2"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2024-Botos-Label-Delay-Online-Continual-Learning.pdf]]"
tags:
  - 延迟标签
  - 持续学习
  - 记忆采样
  - 类型/论文
key_finding: "IWMS 在显式标签延迟协议下，用当前未标注样本的预测类别和特征相似度从已标注记忆中选择回放样本。"
method: "Importance Weighted Memory Sampling（IWMS）"
baseline: "Naive、ER、伪标签、自监督学习和测试时适应"
aliases: [IWMS, Label-Delay-OCL, Botos2024-IWMS]
---

# Label Delay in Online Continual Learning

> Botos 等，NeurIPS 2024；全文 37 页。本文依据 MinerU 分页提取和原 PDF 核对。

## 一句话

论文把数据到达与标签到达分离：时刻 `t` 看见未标注 `x^t`，同时只收到 `t-d` 的标签；IWMS 用最新未标注流指导已标注记忆采样。

## 方法核心

第 3 节算法 1 的时序合同规定：当前输入先预测，延迟标签到达后才训练；当前测试标签只用于评价。第 4 节算法 2 的 IWMS 分两阶段：

1. 对当前未标注样本预测类别，只在记忆中筛选真实标签与预测类别一致的样本。
2. 计算当前样本与候选记忆样本表示的余弦相似度，并按相似度构成的多项分布抽取回放样本。

论文第 4 节明确写出相似度：

\[
K_{i,j}=\cos\big(h(x_i^t),h(x_j^M)\big),
\]

其中 `h` 是分类头之前的特征提取器。为减少开销，论文缓存评估前向得到的记忆特征；第 6.1 节称相似度计算成本相对推理低，并保持与 Naive 相同的反向更新预算。

## 实验结果

- 实验覆盖 CLOC、CGLM、FMoW 和 Yearbook，核心指标为 Online Accuracy 与延迟恢复率 `R_d*`，不是 LAMDA 的 AP/FPR/FNR。
- 论文报告 IWMS 在三类数据集上较 Naive 更稳定，Yearbook 上收益有限；补充材料分析了两阶段筛选、记忆容量和训练时间。
- 这些结果证明的是延迟标签协议下的记忆相关性，不是 Android 恶意软件或 LAMDA 的本地效果。

## 与 LAMDA 的关系

- IWMS 只有在本项目另行冻结“标签延迟”数据合同时才是直接候选；当前年度标签在训练阶段到达，不能为了使用 IWMS 临时引入延迟。
- 如果建立延迟标签子协议，必须显式记录 `available_at`：延迟到期前可用未标注输入，不可用真实标签；只能从已合法到达的历史标记记忆采样。
- 当前双玩家主线不采用 IWMS：它解决的是“延迟标签下回放谁”，不是 FPR 约束或当前恶意漏判修复。

## 不可直接声称

- 其他数据集的 Online Accuracy 不能转述为 LAMDA 结果。
- 不得使用尚未到达的当前标签构造 IWMS 采样或训练代理。
- 不得把 IWMS 作为当前固定标签合同下的公平 ER 直接臂。

## 文献信息

- arXiv：https://arxiv.org/abs/2312.00923
- NeurIPS PDF：https://papers.neurips.cc/paper_files/paper/2024/file/d8f5f134febb4bd74d8f79e338de382c-Paper-Conference.pdf
- 关键位置：第 3 节算法 1；第 4 节算法 2 与 IWMS；第 5 节延迟观察；第 6 节方法比较；附录 A.11、A.14、A.16。
