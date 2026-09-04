---
title: "Closing the Approximation Gap of Partial AUC Optimization: A Tale of Two Formulations"
authors: [Yangbangyan Jiang, Qianqian Xu, Huiyang Shao, Zhiyong Yang, Shilong Bao, Xiaochun Cao, Qingming Huang]
year: 2025
date: 2026-09-04
journal: "arXiv preprint arXiv:2512.01213（2025-12-01）"
source_pdf: "[[raw/papers/methodology/ranking/2025-Jiang-Partial-AUC-Two-Formulations-arXiv.pdf]]"
sha256: "04915f2cb9ef5a7bb75e263ca5550938f3ae171e517c2d8303119eca19feba37"
tags:
  - Partial AUC
  - 阈值学习
  - 泛化界
  - softplus平滑
  - 类型/论文
key_finding: "把 PAUC 的 top-k 实例选择转化为无需排序的阈值学习问题（Theorem 2），用 softplus 平滑硬指示函数 [·]₊，得到逐样本线性计算复杂度、O(ε^(-1/3)) 收敛速率的求解算法；用局部 Rademacher 复杂度给出紧泛化界 Õ(α^(-1)n₊^(-1)+β^(-1)n₋^(-1))（Theorem 5），显式刻画 TPR/FPR 约束 α/β 对泛化的影响。"
method: "先建立实例级（instance-wise）等价问题去除显式正负样本配对（Theorem 1，降低时间复杂度到逐样本线性），再把 top-k 选择转为可微的阈值学习问题（Theorem 2），最后用 softplus surrogate r_κ(x)=log(1+e^{κx})/κ 光滑化 [·]₊ 处理非光滑性（κ 越大越逼近硬指示函数）。"
baseline: "既有 PAUC 优化方法（含成对形式的方法，存在不可控近似误差或可扩展性受限的问题）"
aliases:
  - Jiang2025-PAUCTwoFormulations
---

# 消除 Partial AUC 优化的近似误差：两种重构

> Jiang, Xu, Shao, Yang, Bao, Cao, Huang，2025，arXiv:2512.01213（2025-12-01）· 正文约 16 物理页

## 一句话

把 PAUC（部分 AUC）优化中"选出特定 FPR/TPR 区间内的样本"这一 NP-hard 组合选择问题，转化为可微的阈值学习问题并用 softplus 光滑化，得到逐样本线性复杂度、`O(ε^(-1/3))` 收敛速率的算法，并给出显式依赖约束 `α/β` 的紧泛化界。

## 论文原结论

- 摘要：PAUC 计算中"在约束区间内选实例"是 NP-hard，需要近似技术；本文给出两种简单的**实例级极小极大重构**：一种渐近误差消失，另一种以更多变量为代价保持无偏；关键思路是先建立实例级等价问题降低时间复杂度、用阈值学习简化复杂的样本选择过程、再应用不同平滑技术；所得算法逐迭代计算复杂度对样本量线性、收敛速率 `O(ε^(-1/3))`；给出紧泛化界，明确展示 TPR/FPR 约束 `α/β` 对泛化的影响，阶数为 `Õ(α^(-1)n₊^(-1)+β^(-1)n₋^(-1))`。
- 第 5 页（177 行附近）：Theorem 1 去除显式正负样本配对，把成对损失转为实例级；但分位数运算 `1[f(x')≥η̂_β]` 仍需要对负样本排序才能选择——第二个关键步骤（Theorem 2）把 top-k 选择转为选择阈值的学习问题，使分位数运算可微。
- 第 6 页（207 行附近）：处理非光滑性的最简单策略是用光滑 surrogate 替换，本文采用**softplus surrogate** 光滑化 `[·]_+`（`r_κ(x)=log(1+e^{κx})/κ`，`κ` 越大越逼近硬指示函数，`κ` 可作为可学习或按档标定的连续超参数）。
- **Theorem 5（紧泛化界）**：结合局部 Rademacher 复杂度（而非标准 Rademacher 复杂度），OPAUC 泛化界为 `Õ(α^(-1)n₊^(-1)+β^(-1)n₋^(-1))`；TPAUC 有相同阶数的界（附录 E.2），`α=1` 时退化为 OPAUC 情形。原文指出该界证明比既有工作（[21][25][27]）更简单，且既有工作的分析局限于硬阈值函数与 VC 维，忽略约束 `α/β` 的影响，本文首次为实值分数函数给出显式依赖 `α/β` 的紧界。
- Remark 4：该推导可推广到方形合页损失之外的广义凸连续 surrogate（如 logistic、exponential），只需替换 surrogate 相关系数/更新，训练流程本身不变。

## 与本课题的关系（本课题检索目的：BER 极端分位数训练的软化路线与泛化界文献核验）

本文是 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` **Q1.4（低档在总体层面是否良定）、Q2.2（软化路线）、Q3.4（批量足够时是否出现阈值不稳定）的证据来源**：

- 该核查文档把本文负样本项泛化界 `Õ(1/(βn₋))=Õ(1/K)` 代入本课题六档，得出"六档全部很小"（数值范围 `0.00826`–`0.000103`），与 Curi et al. 较松界的临界点对照后判定"低档的困难不在总体统计，在批内估计"（§1.4）。
- 本文 softplus surrogate `r_κ` 被该核查文档列入"软化：把硬阈值换成连续温度/平滑参数"这一覆盖面最广的路线（§2.2 表格），是"六、可执行动作"表 A3 行（用 softplus 光滑 BER 的 hinge `[·]₊`，`κ` 按档标定）的直接文献依据之一，与 Curi et al. 的 SOFT-CVAR、Nemirovski-Shapiro 松弛同族。
- 该核查文档第三节（Q3.4）指出：本文实验设置为 batch 1024、`β∈{0.3,0.5}`（即 `β·n₋^B≈154`），**未报告任何阈值不稳定或梯度爆炸**，与"`1/β` 不对称度随 `β` 增大而急剧减小"的代数事实一致，可作为"批量足够大时该现象不出现"的反向标定，但**不能倒推**本课题极端低 `β` 档（`K_eff<1`）下的行为——本文实验从未触及如此极端的预算水平。
- **证据等级提升**：该核查文档此前把本文标注为 `L3`（仅摘要/定向抽取，未通读全文，"必须先取全文入库才能进入正文引用"）。**本次已下载官方 PDF 并逐段精读全文（Theorem 1/2/5 正文陈述、softplus 定义、Remark 4），满足全文引用门槛**，可以从 L3 升级为 L1 全文证据。

## 证据记录

- 全文：arXiv 预印本 PDF（2025-12-01），正文约 16 物理页；已用 `pdf-converter`（`mineru-open-api extract`）全文转换，逐段核对摘要、方法（Theorem 1/2）、平滑策略（softplus）、泛化界（Theorem 5）与附录 E.2 引用位置。
- 官方链接：<https://arxiv.org/abs/2512.01213>；Web 检索发现该文献已被 IEEE Xplore 收录（文档 ID `11268965`），暗示已被某 IEEE 期刊/会议接收，但页面内容未能取得，**具体期刊/会议名称、卷期页码本次未核实**，正文引用前应另行核对 IEEE Xplore 条目。
- 证据强度：本次为该核查文档**首次升级为本地全文核验**（原 `L3` → `L1`）；单预印本，未见同行评审记录。

## 疑问 / 待验证

- Theorem 5 的完整证明位于附录 E（本笔记核验了正文陈述与附录起始位置，未逐行核对证明细节）。
- 本文未在极端低 `β`（`K_eff<1`）场景下做实验，其泛化界与算法在该区间的实际行为仍属外推，未经实测验证。
