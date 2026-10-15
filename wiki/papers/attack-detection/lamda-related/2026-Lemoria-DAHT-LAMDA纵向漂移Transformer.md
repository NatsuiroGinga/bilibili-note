---
title: "DAHT: A Domain-Aware Hierarchical Transformer for Longitudinal Android Malware Detection under Concept Drift"
authors: "L. Catherine Lemoria, T. Miranda Lakshmi"
year: 2026
date: 2026-08-31
journal: "International Journal of Computational Research in Science and Technology 2(4)（Zenodo DOI 10.5281/zenodo.22206206，非主流 venue，peer-review 可信度存疑）"
source_pdf: "raw/papers/attack-detection/lamda-related/2026-Lemoria-DAHT-LAMDA纵向漂移Transformer.pdf"
tags:
  - Android恶意软件
  - LAMDA
  - 概念漂移
  - Transformer
  - 类型/论文
key_finding: "在 LAMDA 上做「冻结模型前向时间」评测：用学习式 tokenizer 把 4,561 维特征压到 32 token 再过两层四头 Transformer，2013–2018 训练后 2019–2024 不重训；结论并非普遍更优——XGBoost 在 5 个测试年中的 4 年准确率/宏 F1 更高，DAHT 仅 2024 年领先（99.50% acc / 0.6654 宏 F1）。"
---

# DAHT: Domain-Aware Hierarchical Transformer on LAMDA

## 证据等级
**在线全文已下载并 MinerU 精读**（Zenodo 记录 22206206；本地 PDF 已入 `raw/`）。**venue 存疑**：发表于 *International Journal of Computational Research in Science and Technology* 2(4)，非顶会/主流期刊，引用与数值须谨慎；论文本身表述诚实（明确指出自身非普遍更优）。

## 方法与设定（原文章节）
- 数据：**LAMDA**（本文同数据），4,561 维 Drebin 式静态特征，二分类（恶意/良性）。
- 协议：**冻结模型前向时间**——2013/2014/2016/2017/2018 训练一次，2019/2021/2022/2023/2024 直接评测，**不重训、不持续更新**。
- 架构：4,561 维 → 学习式 tokenizer → 32 token×16 维 → 64 维嵌入 → 2 层 4 头 Transformer encoder → 全局平均池化 → 线性二分类（§IV）。
- 结果：**无普遍优势**——XGBoost 在 5 个测试年中的 4 年准确率与宏 F1 更高；DAHT 仅 2024 年领先（acc 99.50% vs XGBoost 98.75%，宏 F1 0.6654 vs 0.5802，ROC-AUC 0.9139）。

## 三问
1. **能否在固定 200 条预算下运行？** **不适用**。它**不使用记忆缓冲**，是冻结模型的静态前向评测，与"固定 200 条持续学习"不是同一问题；无回放预算概念。
2. **能否挂 MLP？** **N/A**。它是 Transformer 架构；且非持续学习方法，不构成缓冲分配对照。
3. **有无公开代码？** **未定位**。

## 与本文第三章的关系
- **是本次检索中唯一在 LAMDA 上评测的新方法**（任务问 2 的直接命中），须记录：说明已有第三方在 LAMDA 上做纵向评测，且方法为**静态冻结前向**而非持续更新。
- 用途：可作"LAMDA 上非持续学习的前向时间基线"引用，或说明"现有 LAMDA 后续工作仍以静态训练为主，持续学习记忆预算方向尚薄"。
- **不宜作本文对照基线**：无记忆预算、非持续学习、架构不同、venue 可信度低。

## 不能直接声称
- 不能引用其 99.50%/0.6654 作为 LAMDA 强基线——venue 未经严格评审，且为单年偶然领先，作者本人亦否定其普遍优越性。
- 其"前向时间不重训"设定与本文"年度顺序到达 + 回放"设定不同，不可混比。
