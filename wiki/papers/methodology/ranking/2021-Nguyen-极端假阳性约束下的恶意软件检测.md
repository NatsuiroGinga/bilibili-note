---
title: "Leveraging Uncertainty for Improved Static Malware Detection Under Extreme False Positive Constraints"
authors: [Andre T. Nguyen, Edward Raff, Charles Nicholas, James Holt]
year: 2021
date: 2026-09-04
journal: "IJCAI-21 第一届自适应网络防御国际研讨会（1st International Workshop on Adaptive Cyber Defense, held with IJCAI 2021）；arXiv:2108.04081（Laboratory for Physical Sciences / Booz Allen Hamilton / University of Maryland, Baltimore County）"
source_pdf: "[[raw/papers/methodology/ranking/2021-Nguyen-Extreme-FPR-Malware-Detection-arXiv.pdf]]"
sha256: "8ed1c493162e9765f03e9da74e26368f5aabb122436df29aff19110f63d93743"
tags:
  - 极端假阳性率
  - 恶意软件检测
  - 不确定性估计
  - 类型/论文
key_finding: "指出评价集规模不足会人为压低可估计的最低 FPR，并给出经验判据：若测试集大小乘以目标 FPR 小于 100 个样本，报告的该档 TPR@FPR 不可信；用集成与贝叶斯不确定性方法在 Sophos 工业级数据集上把实际 FPR=1e-5 处的 TPR 从既有方法的期望 0.69 提升到 0.80，同时指出既有工作的评价协议可能导致误导性结果。"
method: "在多个数据集、模型、特征类型上系统评估不确定性估计（集成、贝叶斯方法）对极端低 FPR 下恶意软件检测性能的影响；同时诊断既有评价协议中因验证/测试集规模不足导致的 FPR 估计不可靠问题。"
baseline: "既有静态恶意软件检测方法在极端低 FPR（1e-5 及更低）下报告的 TPR"
aliases:
  - Nguyen2021-ExtremeFPRMalware
---

# 极端假阳性约束下利用不确定性改进静态恶意软件检测

> Nguyen, Raff, Nicholas, Holt，2021，arXiv:2108.04081 · 正文约 12 物理页

## 一句话

恶意软件检测常要求 FPR 低至 0.01% 或更低，作者首次系统评估不确定性估计（集成、贝叶斯）对该场景的帮助，并独立指出：许多既有工作报告的极低 FPR 档实际上超出了其评价集能可靠估计的范围。

## 论文原结论

- 摘要：把 Sophos 工业级数据集上实际 FPR=1e-5 处的 TPR 从既有方法的期望 0.69 提升到最佳模型类的 0.80；恶意软件检测常需 FPR 低至 0.01% 甚至更低，现代机器学习缺乏现成工具应对。
- **第 5 页 §4.1（评价可靠性判据，本课题核查目的所在）**：
  > "as the validation set size decreases, the ability to estimate the FPR decreases. This causes more errors and a 'shortening' of the curves as it becomes impossible to estimate lower desired FPR rates. ... some prior works have reported FPRs lower than what their dataset could accurately estimate. **If the test set size times the desired FPR is less than 100 samples, it is unlikely the TPR@FPR reported will be an accurate estimate**"（并举例点名 Anderson et al. 2016 存在此问题）。
- 同页另有更严格的示例性说法：**"if you want an FPR of 1:1,000 and you want 1,000 FPRs to estimate the threshold from you would expect to need 1,000² = 1 million examples"**。
- 全文核心贡献是证明集成与贝叶斯方法能同时改善"模型误差识别"、"新恶意软件家族发现"与"极端 FPR 约束下的预测性能"三方面，并系统指出既有评价协议的缺陷。

## 与本课题的关系（本课题检索目的：BER 训练期预算档"是否可估计/是否应放弃"的文献核验）

本文是 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` **Q4（有没有先例主动放弃不可表示的预算档）的主体证据来源**：

- 该核查文档把本文 `N×FPR≥100` 判据代入本课题 `K=N_pop·β` 六档：`[121, 606, 1213, 2426, 4853, 9706]` **全部通过**（最低档 `121` 刚过门槛 `100`，相对标准误约 `9.1%`），据此判定：**"已发表的『砍档』判据不支持砍掉本课题任何一档"**——若要砍档需另找依据，不能援引本判据。
- 该核查文档明确的**边界声明（不可混用）**：本文判据针对**评价集上估计 TPR@FPR 的可靠性**，不直接等价于**训练期批内预算档的可优化性**；本课题的困难来自训练期批内负样本数不足以支撑极端分位数梯度估计，与本文讨论的"部署后评价阶段"性质不同，因此本文只能作为"六档在评价意义上是良定的"这一佐证，**不能**用于支撑或推翻训练期批量下界的判定（该判定的正确文献依据见 Levy et al. 2020 与 Kawaguchi & Lu 2020 两篇笔记）。

## 证据记录

- 全文：arXiv 预印本 PDF，正文约 12 物理页；已用 `pdf-converter`（`mineru-open-api extract`）全文转换，并结合 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` 已核验的页码/原文引用（第 5 页 §4.1）交叉核对。
- 官方链接：<https://arxiv.org/abs/2108.04081>；作者单位含 Laboratory for Physical Sciences（美国国家安全局下属研究实验室）、Booz Allen Hamilton、UMBC。**经 Web 检索核实，本文发表于 IJCAI-21 第一届自适应网络防御国际研讨会**（与 IJCAI 2021 同期举办），该核查文档此前标注的"作者与发表载体未核"已补齐。
- 证据强度：原为该核查文档标注的 `L2`（在线全文已读、原件未入库）；**本次下载官方 PDF 入库后升级为本地全文 `L1`**。

## 疑问 / 待验证

- 已核实发表载体（IJCAI-21 自适应网络防御研讨会），但未核实 arXiv 版本与研讨会正式发表版本在内容上是否有差异。
- 第 5 页判据的推导依据（假阳性数近似 Poisson 分布、相对标准误 `1/√K`）是该核查文档给出的统计等价形式，本文原文是否有更严格的推导本次未逐段核验。
