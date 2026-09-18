---
schema: paper-note-search/v1
title: "Testing for Outliers with Conformal p-values"
title_zh: "用保形 p 值做离群检验"
authors: [Stephen Bates, Emmanuel J. Candès, Lihua Lei, Yaniv Romano, Matteo Sesia]
year: 2023
date: 2026-08-26
journal: "The Annals of Statistics（arXiv:2104.08279 版本，卷期未逐项核验）"
doi: null
arxiv_id: "2104.08279"
fulltext_verified: true
source_pdf: "[[raw/papers/methodology/2023-Bates-Testing-Outliers-Conformal-p-values.pdf]]"
tags: [保形p值, 离群检验, FDR, PRDS, 误报率, 类型/论文]
aliases:
  - Bates2023Outliers
  - 保形p值离群检验
tasks:
  - 离群检验
  - 分布外检验
  - 多重检验下的误报控制
datasets:
  - 真实与模拟数据（§5 数值实验）
methods:
  - 边际保形 p 值
  - 条件化保形 p 值
  - Fisher 合并检验
  - BH 过程
metrics:
  - 误报率 FPR
  - 错误发现率 FDR
key_finding:
  - "Theorem 2（物理第 7 页）证明保形 p 值满足 PRDS，因此 BH 过程可用（Corollary 1，物理第 7 页），这为把 p-filter 一类需要 PRDS 的多层方法用在保形 p 值上提供了依据。"
  - "Proposition 1（物理第 8 页 §3.1）给出边际保形 p 值的逐点 FPR 分布：阈值由校准集决定，FPR 本身是随机的，原文指出即使 1600 个校准点其变异系数仍可观。"
  - "摘要（物理第 1 页）声明其技术还给出任意离群检测算法的 FPR 关于原始统计量阈值的一致置信界，且用集中不等式而非组合论证建立有限样本保证。"
supports:
  - "保形 p 值满足 PRDS，可与 BH 及依赖 PRDS 的多层预算方法组合"
  - "分裂校准得到的阈值其 FPR 是随机量，需要按分布而非按点估计理解"
  - "存在关于阈值一致的 FPR 置信界，可支持事后阈值搜索"
cannot_support:
  - "路径极值或序贯前缀统计量上的误报控制（本文单元是独立测试点）"
  - "组条件或分面 FPR 控制"
  - "把其一致置信界当作本课题逐点 Tong 证书的等价物"
related:
  - "[[2018-Tong-纽曼皮尔逊分类]]"
  - "[[2017-Barber-Ramdas-p-filter多层分组FDR控制]]"
  - "[[2021-Bates-分布无关风险控制预测集]]"
---

# 用保形 p 值做离群检验

> Bates, Candès, Lei, Romano, Sesia, 2023, Annals of Statistics · arXiv:2104.08279 · 81 页（含附录）

## 一句话

把保形 p 值用于离群检验时，多个测试点的 p 值并非独立，但它们满足 PRDS，因此 BH 仍然可用；顺带给出 FPR 关于阈值的一致置信界。

## 全文核验结论

页码取自本地原件 `2023-Bates-Testing-Outliers-Conformal-p-values.pdf` 的物理页。

### 问题与依赖结构（物理第 1 页摘要，第 3 页附近）

`2n` 个 i.i.d. 点，判断新点是否为离群。困难在于：**不同测试点的经典保形 p 值共用同一个校准集，因而互相依赖**，而 FDR 控制通常要求 p 值独立或满足特定正相依。

### Theorem 2：保形 p 值是 PRDS（物理第 7 页）

在 `ŝ(X)` 连续分布的前提下，边际保形 p 值满足 **PRDS**（positive regression dependence on a subset）。

### Corollary 1：BH 可用（物理第 7 页）

由 Theorem 2 与 Benjamini–Yekutieli 结论，BH 过程施于保形 p 值可控制 FDR。

### Proposition 1：逐点 FPR 是随机的（物理第 8 页 §3.1）

§3.1 标题为「Warm up: analyzing the false positive rate」。取 `ℓ = ⌊(n+1)α⌋`，原文给出边际保形 p 值的 FPR 分布（引自其参考文献 [41]）。

**关键定量提醒**：原文指出该分布的**变异系数即使在 1600 个校准点下仍然可观**（物理第 8 页附近），并据此说明边际保形 p 值**在给定校准集条件下可能是反保守的**。

### 一致置信界（物理第 1 页摘要，第 4 页附近）

摘要原文声明其技术「yield a uniform confidence bound for the false positive rate of any outlier detection algorithm, **as a function of the threshold** applied to its raw statistics」。原文另强调其结果「depart from classical conformal inference as we leverage **concentration inequalities rather than combinatorial arguments**」。

## 我的理解

对本课题最有价值的是两点，且方向相反：

- **正面**：Theorem 2 把「保形 p 值 + 需要 PRDS 的多重检验方法」这条路打通了。上一轮 p-filter 笔记里留下的「PRDS 是否成立」疑点，在**保形 p 值**这一侧有了答案。
- **警示**：Proposition 1 说明分裂校准阈值的 FPR 是随机量，条件于校准集可能反保守。这正是 Tong 用 `δ` 显式承认的那件事——本课题的证书路线在这一点上是**对的选择**，因为它把这个随机性写进保证里，而不是假装阈值精确。

## 与本课题的关系

- **部分关闭上一轮疑点 7**：p-filter 的 PRDS 假设在保形 p 值上成立（Theorem 2，物理第 7 页）。但本课题的实体级统计量是 **Tong 次序统计量证书**而非保形 p 值，**能否直接继承 PRDS 仍待验证**——两者构造不同。
- **支持证书路线的必要性**：Proposition 1 的变异系数提醒是「不能用经验分位数替代证书」的独立佐证，与 Tong 2018 的论证同向。
- **阈值搜索的合法性**：一致置信界给出了「事后搜索阈值」的合法机器。本课题当前按 Tong 规矩**预先固定 `k`**，不搜索；若将来需要搜索，这是可用的工具。
- **不是路径极值的近邻**：本文单元是独立测试点，不处理序贯前缀或路径极值。

## 论文可以支持

- 保形 p 值满足 PRDS，可与 BH 及依赖 PRDS 的多层方法组合。
- 分裂校准阈值的 FPR 是随机量，需按分布理解；条件于校准集可能反保守。
- 存在关于阈值一致的 FPR 置信界，支持事后阈值搜索。

## 论文不能支持

- 不能说本文处理了路径极值或序贯前缀统计量上的误报控制。
- 不能说本文做了组条件或分面 FPR 控制。
- 不能把 Theorem 2 的 PRDS 结论直接搬给本课题的 Tong 次序统计量证书——构造不同，须单独验证。

## 实验结果与负证据

- **负证据（Proposition 1，物理第 8 页）**：边际保形 p 值的 FPR 变异系数在 `1600` 个校准点下仍可观，且条件于校准集可能反保守。这是对「校准集够大就不用证书」这一直觉的直接反驳。
- **依赖性问题（物理第 3 页附近）**：共用校准集使不同测试点的 p 值互相依赖，朴素套用独立性假设的多重检验会出问题；Theorem 2 才使 BH 合法。
- **§5 数值实验**：真实与模拟数据上比较边际与条件化保形 p 值。**本笔记未逐项核验其数值**，不引用具体数字。

## 疑问 / 待验证

- 本课题的实体级 Tong 证书统计量是否也满足 PRDS？若成立，p-filter 的多层免均分结果可望迁移，这是关闭 `δ` 均分疑点的一条具体路径。
- 期刊卷期与 DOI 未逐项核验，当前只登记 arXiv 标识。

## 文献信息

- arXiv:2104.08279
- 期刊：Annals of Statistics（卷期与 DOI 未核验，`doi` 字段留空）
- Zotero：待导入（本轮 MCP 连接被拒，见 `notes.md` §8 阻塞记录）
