---
schema: paper-note-search/v1
title: "Distribution-Free, Risk-Controlling Prediction Sets"
title_zh: "分布无关的风险控制预测集"
authors: [Stephen Bates, Anastasios Angelopoulos, Lihua Lei, Jitendra Malik, Michael I. Jordan]
year: 2021
date: 2026-08-26
journal: "Journal of the ACM, 68(6), Article 43"
doi: "10.1145/3478535"
arxiv_id: "2101.02703"
fulltext_verified: true
source_pdf: "[[raw/papers/methodology/2021-Bates-Distribution-Free-Risk-Controlling-Prediction-Sets.pdf]]"
tags: [风险控制, 上置信界, ClopperPearson, 容忍区, 分布无关, 类型/论文]
aliases:
  - RCPS
  - Bates2021
  - Risk-Controlling Prediction Sets
tasks:
  - 风险控制
  - 阈值校准
  - 集合预测
datasets:
  - 图像分类与分割等视觉任务（§5 实验）
methods:
  - UCB 校准
  - Hoeffding 界
  - Bentkus 界
  - Hoeffding-Bentkus 界
  - 精确二项（Clopper-Pearson 型）界
  - Waudby-Smith-Ramdas 界
metrics:
  - (γ, δ) 风险控制
  - 集合大小
key_finding:
  - "Definition 1（物理第 2 页）把 (γ, δ) 风险控制预测集定义为以至少 1-δ 概率满足 R(T) ≤ γ，与本课题 Tong 证书同型。"
  - "Theorem 1（物理第 5 页）：损失单调且有逐点上置信界时，数据驱动选阈值 λ̂ 仍保证 (γ, δ) 有效；单调性是把逐点收敛转为有效性的关键。"
  - "Remark 4（物理第 7 页）与附录 B Theorem B.1（物理第 29 页）：损失取值仅为 {0,1} 时精确二项上界最紧，原文称 should always be used，且较 Bentkus 界改进一个 e 因子。"
supports:
  - "本课题对 0/1 误报损失采用 Clopper-Pearson 精确二项上界有直接文献依据"
  - "(γ, δ) 双参数证书是通用且已形式化的风险控制形式"
  - "风险关于阈值单调时可在数据上搜阈值而不损失有限样本保证"
cannot_support:
  - "组条件或分层风险控制（本文是池化的单一 (γ, δ)）"
  - "非交换或跨年迁移下的保证（校准与测试仍需同分布）"
  - "非单调风险下的阈值选择（属后续 Learn-then-Test 范围）"
related:
  - "[[2018-Tong-纽曼皮尔逊分类]]"
  - "[[2024-Angelopoulos-保形风险控制]]"
  - "[[2012-Vovk-条件归纳保形预测]]"
---

# 分布无关的风险控制预测集

> Bates, Angelopoulos, Lei, Malik, Jordan, 2021, JACM 68(6):43 · 34 页

## 一句话

本课题 Tong 证书所用的「经验风险 + 精确二项上界 + `δ`」这套机器，在这篇论文里被抽象成通用的 UCB 校准框架，并明确背书二元损失下用精确二项界。

## 全文核验结论

页码取自本地原件 `2021-Bates-Distribution-Free-Risk-Controlling-Prediction-Sets.pdf` 的物理页。

### Definition 1：`(γ, δ)` 风险控制预测集（物理第 2 页）

> `T` 是 `(γ, δ)`-risk-controlling prediction set，若以至少 `1 − δ` 的概率有 `R(T) ≤ γ`。

原文注明 `(γ, δ)` 由用户**预先**选定，并称 `δ` 的代表性取值可想成 `10%`。

**这正是本课题 Tong 证书的双参数形式**：`γ` 对应实体级误报预算 `q`，`δ` 对应证书失效概率。

### Theorem 1：UCB 校准的有效性（物理第 5 页）

设 `{T_λ}` 为满足嵌套性的集合预测子族，损失满足单调性条件。若对每个 `λ` 有逐点上置信界

```
P{ R(λ) ≤ R̂⁺(λ) } ≥ 1 − δ                      （物理第 5 页式 (3)）
```

取

```
λ̂ = inf{ λ ∈ Λ : R̂⁺(λ') < γ , ∀λ' ≥ λ }        （物理第 5 页式 (4)）
```

则 `P{ R(T_λ̂) ≤ γ } ≥ 1 − δ`，即 `T_λ̂` 是 `(γ, δ)`-RCPS。

原文强调关键在**风险函数的单调性**：正因单调，才能把逐点收敛结果转成「数据驱动选 `λ`」的有效性；否则需要一致收敛结果。

### 上置信界族（物理第 6–7 页）

| 界 | 适用 | 备注 |
|---|---|---|
| 简化 Hoeffding（Prop 1，Thm 2） | 损失有上界 1 | 最松，作热身 |
| 更紧 Hoeffding（Prop 3） | 同上 | `h₁(t;R) ≥ 2(t−R)²` |
| Bentkus（Prop 4） | 同上 | 二项分布为最坏情形（差一小常数）；二元损失下近乎紧 |
| **Hoeffding–Bentkus**（Thm 3，物理第 6 页） | 通用有界损失 | 二者取优 |
| Waudby-Smith–Ramdas（§3.1.3） | 非二元损失 | 自适应方差，HB 在低方差时很松 |

### Remark 4 与 Theorem B.1：二元损失用精确二项（物理第 7 页、第 29 页）

**Remark 4**（物理第 7 页）原文：

> The Bentkus inequality is closely related to an exact confidence region for the mean of a binomial distribution. In the special [case] where the loss takes values only in {0, 1}, **this exact binomial result gives the most precise upper confidence bound and should always be used**; see Appendix B.

**附录 B「An Exact Bound for Binary Loss」**（物理第 29 页）给出构造：损失取 `{0,1}` 时逐点损失是 Bernoulli，风险即其均值，

```
g_bin(t; R(λ)) = P( Binom(n, R(λ)) ≤ ⌈nt⌉ )
R̂⁺_bin(λ) = sup{ R : g_bin( R̂(λ); R ) ≥ δ }
```

即**反转二项尾概率**得到上置信界——这就是 Clopper–Pearson 型精确上界。原文称该表达式与 Bentkus 界相同但**改进了一个 `e` 因子**。

**Theorem B.1**（物理第 29 页）：二元损失下 `T_λ̂bin` 是 `(γ, δ)`-RCPS。原文并注明二元损失情形归结为**经典容忍区**。

## 我的理解

这篇论文的价值不在于提出新界，而在于**把「选阈值」这件事的合法性条件说清楚**：只要风险随参数单调、且有逐点 UCB，就可以在数据上搜阈值而不损失有限样本保证。

对本课题最直接的一句话是 Remark 4：我们的损失是「良性实体被告警」的 0/1 指示，精确二项上界是**最紧且应当始终采用**的选择——这为本课题用 CP 而非 Hoeffding 提供了直接文献依据。

## 与本课题的关系

- **为 CP 的选择提供文献依据**：本课题的实体级误报是 0/1 损失，Remark 4（物理第 7 页）与附录 B（物理第 29 页）直接支持用精确二项上界。此前只有数学论证，现有全文依据。
- **`(γ, δ)` 形式同型**：Definition 1 与本课题的 `(q, δ')` 证书同构。
- **单调性是前提**：Theorem 1 要求风险关于阈值参数单调。本课题按分数阈值判告警，FPR 关于阈值单调，条件满足；但**路径最大统计量**下的单调性需单独核验，标为**待验证**。
- **本课题的差量**：RCPS 是**池化**的单一 `(γ, δ)`，不做分组；本课题为每个长度桶各签一份证书。RCPS 全文**未处理组条件或分层预算分配**。

## 论文可以支持

- **CP 的选择有文献依据**：Remark 4（物理第 7 页）明确二元损失下精确二项上界最紧且「should always be used」；附录 B（物理第 29 页）给出反转二项尾概率的构造与 Theorem B.1。本课题的实体级误报正是 0/1 损失。
- **`(γ, δ)` 形式已形式化**：Definition 1（物理第 2 页）与本课题 `(q, δ')` 证书同构。
- **数据驱动选阈值的合法性条件**：Theorem 1（物理第 5 页）指出单调性加逐点 UCB 即可，无需一致收敛。
- **二元损失归结为经典容忍区**：附录 B 末明确这一等价（物理第 29 页）。

## 论文不能支持

- 不能说 RCPS 提供了组条件或分层风险控制——它是池化的。
- 不能说 RCPS 处理了非交换或跨年迁移——Remark 2 只放宽了「拟合初始模型的数据可来自不同分布」，仍要求校准数据与测试数据同分布。
- 不能把 Theorem 1 用在非单调风险上；那是后续 Learn-then-Test 的范围（未入库）。

## 实验结果与负证据

- **界的强弱次序（物理第 6–7 页，§3.1）**：简化 Hoeffding 最松；更紧 Hoeffding（Prop 3）改进之；Bentkus（Prop 4）在二元损失下近乎紧；Hoeffding–Bentkus（Thm 3）取二者之优；**精确二项在二元损失下最紧，较 Bentkus 改进一个 `e` 因子**（附录 B，物理第 29 页）。
- **HB 界的失效方向（§3.1.3）**：非二元损失且方差小时 HB 很松，需改用 Waudby-Smith–Ramdas 界。本课题损失为二元，不受此限。
- **对本课题的边界**：全文**未处理组条件、分层预算或跨组 `δ` 分配**。逐桶各自 UCB 校准时 `δ` 如何分配，本文不作答；p-filter 给出的是 FDR 语义下的对应答案。
- **§5 视觉任务实验**：多种损失下评估 UCB 校准表现。**本笔记未逐项核验该节数值**，不引用其具体数字。
- **待核的单调性前提**：本课题的路径最大统计量下，风险关于阈值是否仍单调未验证；若不单调，Theorem 1 不适用。

## 疑问 / 待验证

- 路径最大统计量下风险关于阈值是否仍单调？若不单调，须改用 Learn-then-Test 式的多重检验路线。
- 逐桶各自做 UCB 校准时，`δ` 如何在桶间分配才不过度保守？RCPS 未讨论，p-filter 给出 FDR 语义下的对应答案。

## 文献信息

- DOI：`10.1145/3478535`
- arXiv:2101.02703
- 代码：`github.com/aangelopoulos/rcps`（未核）
- Zotero：`7YL8GW7G`
