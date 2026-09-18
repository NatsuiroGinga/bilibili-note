---
title: "Proxy-Lagrangian：不可微速率约束与双玩家优化"
date: 2026-09-09
tags: [约束优化, FPR约束, 双玩家, LAMDA近邻]
source_pdf: "raw/papers/attack-detection/lamda-related/2019-Cotter-Proxy-Lagrangian-Non-Differentiable-Constraints-JMLR.pdf"
---

# Proxy-Lagrangian：不可微速率约束与双玩家优化

题录：Andrew Cotter 等，JMLR 20(172)，2019，arXiv:1809.04198。

原件 SHA-256：3a1b5629dcee2c828ba4f04f6d9022360f20402aaaa41b6eeb12f21396738a32。

方法：把 targeted FPR、recall、precision 和 churn 写成速率约束；普通拉格朗日方法在非凸、不可微约束下可能没有纯均衡，Proxy-Lagrangian 用代理约束和双玩家博弈求近似混合均衡，并可收缩为至多 m+1 个确定性模型。

LAMDA 映射：模型玩家优化当前监督、Replay 和恶意漏判修复，约束玩家处理独立良性集合的 FPR。训练代理不等于真实二值 FPR，未知未来年份也没有保证。

官方代码：https://github.com/google-research/tensorflow_constrained_optimization（仓库已归档）。

证据等级：E2；原件已下载并由 MinerU 分段解析，尚无 LAMDA 本地实验支持。
