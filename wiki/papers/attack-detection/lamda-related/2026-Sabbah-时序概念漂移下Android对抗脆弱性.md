---
title: "时序概念漂移下的对抗脆弱性：Android 恶意软件检测的纵向研究"
authors: [Ahmed Sabbah, Mohammed F. Kharma, Radi Jarrar, Samer Zein, David Mohaisen]
year: 2026
date: 2026-10-15
journal: "arXiv 2605.23623（预印本）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2026-Sabbah-Adversarial-Temporal-Concept-Drift-Android.pdf]]"
tags: [Android恶意软件, 概念漂移, 对抗鲁棒性, 年度切片, 纵向研究, 类型/论文]
key_finding: "跨十余年 Android 应用做纵向漂移感知的对抗鲁棒性评测：数据按年切片，用 same-year / cross-year / expanding-window 三种部署协议，FGSM 与 SPSA 攻击下清洁与对抗准确率随训练-测试年差增大而下降，expanding-window 重训减缓但不消除鲁棒性损失。"
---

# 时序概念漂移下的对抗脆弱性：Android 恶意软件检测的纵向研究

## 全文核验结论

- 问题（摘要，物理第 1 页）：真实部署中良性与恶意应用结构与行为持续变化，产生**非平稳数据分布**；对抗扰动又叠加一层脆弱性；二者**交互**研究不足。
- 数据与协议（摘要、第 1–2 页）：
  - 十余年 Android 应用，用模拟器与真机执行抽取**静态与动态特征**；
  - 数据按**年切片**（yearly slices）；
  - 三种部署协议模拟真实学习场景：(1) **same-year** 训练与测试；(2) **cross-year** 跨年部署、无历史（无模型更新）；(3) **expanding-window** 用累积历史重训。
- 攻击与度量（摘要，第 1 页）：多分类器家族上生成 **FGSM** 与 **SPSA** 对抗样本（带可行性约束）；测量清洁性能、对抗准确率（AA）、攻击成功率（ASR），并提出时序关联指标 **RobustDrop、ΔASR、Adversarial Amplification Factor（AAF）**。
- 主要发现（摘要，第 1–2 页）：训练-测试年差增大 → 清洁准确率与对抗准确率**下降**，ASR 依配置上升（FGSM、静态特征下尤甚）；**expanding-window 重训减缓但不消除**持续分布演化下的鲁棒性损失；主张长期评估须纳入时序漂移。

## 对本课题（LAMDA 年度漂移）的合法映射

- 这是本课题「**年度切片 + 跨年部署**」评测协议的**直接近邻与协议先例**：
  - same-year / cross-year / expanding-window 三协议与本课题「按年评估 + 未来年泛化」高度同构，可作为**评测协议措辞与对照设置**的来源；
  - 「expanding-window 缓解但不消除」提示：仅靠累积重训不足以解决年度漂移——这为本课题「需要更强的训练目标」提供了旁证（但这是**对抗鲁棒性**维度的证据，非清洁准确率维度，不可直接等同）。
- 差异：本文焦点是**对抗脆弱性**（FGSM/SPSA），**不是**训练目标（无 DRO/group 方法）；不能据本文支持「group 目标有增益」。

## 原创边界与不能直接声称

- 「年切片 + 跨年/扩展窗口协议 + 漂移下鲁棒性评测」已被本文覆盖为**评测方法论**；本课题若照用该协议，须引用为协议来源，不能当作自创。
- 本文为预印本（arXiv, 2026-05），数值为**作者自报**，未在本仓复现；不得作为正文确定性论断。
- 本文只做评测，不提出训练方法；不构成对本课题方法增益的支持或否证。

## 证据记录

- 全文状态：已下载并逐页核验（摘要、Introduction、协议描述）。
- 稳定标识：arXiv `2605.23623`；预印本（Elsevier 期刊投稿版，见 ScienceDirect S0957417426024693）。
- 同组另一件：`raw/papers/attack-detection/lamda-related/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf`（同第一作者，主题相邻）。
- 课题角色：第四章评测协议先例；「仅累积重训不足」的旁证来源。
