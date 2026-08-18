---
title: "Label Alignment Regularization for Distribution Shift"
authors: [Ehsan Imani, Guojun Zhang, Runjia Li, Jun Luo, Pascal Poupart, Philip H. S. Torr, Yangchen Pan]
year: 2024
date: 2026-08-12
journal: "Journal of Machine Learning Research 25(247)"
source_pdf: "[[raw/papers/methodology/2024-Imani-Label-Alignment-Regularization.pdf]]"
zotero_key: BNQVGJ6Q
zotero_key: BNQVGJ6Q
tags: [无监督域适应, 分类头, 谱方法, 分布移位, 类型/论文]
key_finding: "标签对齐正则只调整分类头并把目标预测限制到目标顶端谱子空间，但原实验依赖少量目标标签选正则强度。"
method: "源尾部隐式正则消除与目标谱子空间正则"
baseline: "线性与浅层二分类域适应基线"
aliases: [LAR, Imani2024-LAR]
related: ["[[EhsanEI-LAR官方源码]]"]
---

# 标签对齐正则

## 论文原结论

正文第 4 节公式（6）在源平方损失中去除源尾部隐式谱正则，并惩罚目标预测在低奇异值子空间的分量；算法 1 对源、目标协方差做特征分解。第 5 节在论文假设下证明解位于目标顶端右奇异向量张成空间。

## 可迁移机制

冻结表示、仅校正头部是不同于 DANN/CORAL/MMD 的低成本作用层，可先在现有缓存上证伪。谱残差、目标有效秩和排序改变率均可观测。

## 本课题推论

可构造“恶意排序方向保留的谱头校正”：目标顶端子空间约束之外，保留源恶意对困难良性的成对次序。该实质修改仍需证明能非单调地改变目标排序；纯单调概率校准直接淘汰。

## 不可直接声称

原论文使用少量目标标签选正则强度，不满足 LSPR24 无标签前缀合同；稀有恶意方向可能处在低方差子空间并被投影掉。不能依据谱定理宣称 PR-AUC 改善。

## 待验证

叶线性替代头必须先达到 XGBoost 目标 PR-AUC 的预注册保真门槛，否则无需进入谱校正。

## 文献信息

- JMLR：https://www.jmlr.org/papers/v25/23-0899.html
- arXiv：2211.14960
