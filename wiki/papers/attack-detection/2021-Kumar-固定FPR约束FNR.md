---
title: "Implicit Rate-Constrained Optimization：固定 FPR 下的 FNR"
date: 2026-09-09
tags: [FPR约束, FNR, 不可分解指标, LAMDA近邻]
source_pdf: "raw/papers/attack-detection/lamda-related/2021-Kumar-Implicit-Rate-Constrained-Optimization.pdf"
---

# Implicit Rate-Constrained Optimization：固定 FPR 下的 FNR

题录：Abhishek Kumar、Harikrishna Narasimhan、Andrew Cotter，ICML 2021，arXiv:2107.10960。

原件 SHA-256：a7339b238217bf20711d4a5f1df01f89ba2840d5f4ee933e377362352ca4d24d。

方法：研究给定 FPR 下最小化 FNR 等非可分解目标，通过隐函数把阈值表示为模型参数函数，再用梯度方法优化约束目标。

LAMDA 映射：可作为固定 FPR operating point 的理论近邻；由于本项目已有固定阈值合同，不直接替换阈值。必须比较普通训练、等 FPR 阈值匹配和约束训练。

官方代码：https://github.com/google-research/google-research/tree/master/implicit_constrained_optimization

证据等级：E2；原件已下载并由 MinerU 解析，尚无 LAMDA 本地实验支持。
