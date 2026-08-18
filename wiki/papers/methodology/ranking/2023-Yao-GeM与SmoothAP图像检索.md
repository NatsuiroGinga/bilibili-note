---
title: "Learning global image representation with generalized‐mean pooling and smoothed average precision for large‐scale CBIR"
authors: [Jinliang Yao, Yongqing Li, Bing Yang, Chenrui Wang]
year: 2023
date: 2026-08-13
journal: "IET Image Processing 17(9):2748–2763"
source_pdf: "[[raw/papers/methodology/ranking/2023-Yao-GeM-SmoothAP-IET.pdf]]"
sha256: "3b9188f6d31a04bf1385dda111fa31a064f8d64666cb66df8adb10c3500adc8d"
tags:
  - 广义均值池化
  - 平滑平均精确率
  - 图像检索
  - 类型/论文
key_finding: "提出 GS，将 GeM 池化与基于 sigmoid 排名近似的 Smooth-AP 直接组合；因此“GeM/Lp＋平滑 AP”已有题名级和公式级直接先例。"
method: "ResNet50 产生特征图，GeM 聚合成全局描述子，再以 Smooth-AP 列表损失训练；GSA 进一步联合 ArcFace 分类损失。"
baseline: "GeM(AP)、GeM(CL)、GeM(O)、R-MAC、SPoC、CroW 及局部描述子方法"
aliases:
  - Yao2023-GeM-SmoothAP
  - GS
  - GSA
---

# GeM 与 Smooth-AP 的大规模图像检索组合

> Yao、Li、Yang、Wang，2023，IET Image Processing · 16 个物理页 · DOI `10.1049/ipr2.12825` · Zotero 规范条目 `W7FTP9TU`（文献库另有自动导入重复项，未擅自删除）

## 论文原结论

- 物理第 1 页题名、作者、DOI 与版权行核验：开放获取，Creative Commons Attribution-NonCommercial，版权为作者所有并由 Wiley 代表 IET 出版。
- 物理第 4 页公式（5）给出 GeM：对空间特征取 `p` 阶均值后开 `1/p` 次方，并称 `p` 为可训练超参数；同页又说明实验按前作经验设 `p=3.0`。因此不能仅凭该文断言其报告结果确实学习了 `p`。
- 物理第 5—6 页公式（7）—（12）给出 AP、排名函数、sigmoid 平滑和最终 `1−mAP` 损失，形成 GeM＋Smooth-AP 的端到端管线。
- 物理第 8 页表 2直接比较 `GeM(AP)`、GS 与 GSA；物理第 14 页局限部分承认列表 AP 强依赖大批量，且单卡批量限制性能。
- 物理第 14 页作者声称首次组合 GeM 与直接 AP，但其表 2和参考文献已把 Revaud 等 2019 的 `GeM(AP)` 作为先例；本审计不采信这一宽泛“首次”措辞，只把本文视为 GeM＋Smooth-AP 的直接证据。

## 与本课题的关系

- **被占用点**：`Lp`／GeM 池化与平滑 AP 联合训练、端到端 AP 损失、以及“减少硬样本挖掘”的叙事均不能作为本课题原创。
- **关键差异**：图像内空间位置不是按实体均匀抽样的有限流总体；本文无无放回 K 流估计、有限总体方差、Horvitz–Thompson／Hansen–Hurwitz 校正、跨年度安全任务或因果历史。
- **仍可主张**：实体目标测度与两级设计型抽样的任务特定推导、因果上下文兼容的矩估计，以及 AP 复合梯度偏差控制。
- **实验待证**：上述新增边界是否产生实体 AP 增益，而不是普通 GeM＋Smooth-AP 的迁移效果。

## 证据记录

- 全文：用户提供的 Wiley 正式 PDF，16 页；已核验题名、作者、DOI、许可、公式（5）、公式（7）—（12）、表 2及局限部分。
- 出版社页：<https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/ipr2.12825>
- 原件哈希：`3b9188f6d31a04bf1385dda111fa31a064f8d64666cb66df8adb10c3500adc8d`。
- 证据强度：完整全文直接近邻；不构成本项目效果证据。

