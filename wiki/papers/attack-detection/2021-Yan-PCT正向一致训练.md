---
title: "Positive-Congruent Training：正向一致训练与 Focal Distillation"
date: 2026-09-09
tags: [持续学习, 安全回归, PCT, LAMDA近邻]
source_pdf: "raw/papers/attack-detection/lamda-related/2021-Yan-PCT-Regression-Free-Model-Updates-CVPR.pdf"
---

# Positive-Congruent Training：正向一致训练与 Focal Distillation

题录：Sijie Yan 等，CVPR 2021，pp. 14299--14308，arXiv:2011.09161。

原件 SHA-256：8487b8afa1f272c4a3e37ab44e9b1b3ffad8030d9e6b7342dd7eaba2e9fdae5f。

方法：以旧模型正确样本指示量增加蒸馏权重。公式（4）为交叉熵加正向一致损失；公式（7）定义 Focal Distillation；公式（8）为温度缩放 KL；公式（9）为 logit 平方距离。图像实验使用 alpha=1、beta=5，温度约 100 时接近 logit matching。

LAMDA 边界：PCT 只保护旧正确决策，不能单独修复当前恶意漏判，也不提供 FPR 保证。应与恶意漏判集合和独立 FPR gate 分开消融。

官方代码：https://github.com/amazon-science/regression-constraint-model-upgrade

证据等级：E2；原件已下载并由 MinerU 完整解析，尚无 LAMDA 本地实验支持。
