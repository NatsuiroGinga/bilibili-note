---
title: "When AUC Meets DRO: Optimizing Partial AUC for Deep Learning with Non-Convex Convergence Guarantee"
authors: [Dixian Zhu, Gang Li, Bokun Wang, Xiaodong Wu, Tianbao Yang]
year: 2022
date: 2026-08-28
journal: "ICML 2022，PMLR 162:27548–27573"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO-ICML.pdf]]"
sha256: "ce0c5e4494774de414d5844cc69f05cbf351961a11dd83460b357744a93d8b40"
arxiv_id: "2203.00176"
tags: [部分AUC, 低误报, 分布鲁棒优化, 深度排序, 类型/论文]
key_finding: "论文已用 CVaR/KL-DRO 为每个正样本构造顶部负样本风险，并给出深度 one-way/two-way pAUC 随机优化；低误报排序本身不是本课题创新。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# pAUC-DRO：低误报深度排序

## 题录与源码

- ICML 2022 正式论文，PMLR 162:27548–27573。
- 方法已进入 LibAUC：<https://github.com/Optimization-AI/LibAUC>，官方文档提供 `pAUCLoss` 教程。

## 全文证据

- 物理第 3 页公式（1）–（3）定义 FPR 区间内 one-way pAUC 与同时限制 TPR/FPR 的 two-way pAUC。
- 物理第 4 页公式（7）–（10）把顶部负样本选择写为 DRO：CVaR 给精确非平滑估计，KL 正则给平滑软估计。
- 物理第 5–6 页算法 1–3 为 SOPA、SOPA-s 与 SOTA-s，并给出收敛条件。
- 实验在图像和分子数据上比较 CE、AUC、p-norm push、朴素小批量与提出算法；表 1–4 位于物理第 9 页。
- 物理第 8 页先以 CE 预训练，再重置分类头并用 pAUC 目标微调全部层；论文没有把 CE 与 pAUC 以权重 1 并列为辅助损失。

## 新颖性边界

- 已占用：深度低误报排序、顶部良性样本聚焦、精确/平滑 pAUC 估计及随机优化。
- 未覆盖：实体袋、严格因果前缀、等实体而非等流测度、LSPR 源年冻结预算。
- D2 必须将本文作为原组件对照，并证明任务化改造相对普通 pAUC 的增益；普通 pAUC 不能称创新。
