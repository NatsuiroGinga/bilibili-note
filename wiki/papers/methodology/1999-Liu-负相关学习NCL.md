---
title: "Simultaneous Training of Negatively Correlated Neural Networks in an Ensemble"
authors: [Yong Liu, Xin Yao]
year: 1999
date: 2026-10-21
journal: "IEEE Transactions on Systems, Man and Cybernetics, Part B (Cybernetics), 29(6):716–725"
source_pdf: "[[raw/papers/methodology/1999-Liu-NegativeCorrelationLearning.pdf]]"
sha256: "de7e5d3d74471bb161a672c146a6c80e119eb8a0ca21484408a002bdbe88cfe3"
doi: "10.1109/3477.809027"
tags:
  - 负相关学习
  - NCL
  - 集成多样性
  - 偏差方差协方差
  - 类型/论文
key_finding: "在同时训练的集成中给每个成员的误差函数加相关惩罚项 $E_i=\\frac1N\\sum_n[\\frac12(d-F_i)^2+\\lambda p_i]$，$p_i$ 为自身偏差与其余成员偏差之和的乘积；最小化 $p_i$ 使成员误差负相关。$0\\le\\lambda\\le1$：无噪声回归中 $\\lambda\\approx0.9$ 时集成 MSE 最小（物理第 719 页），噪声条件下 $0<\\lambda\\le0.75$ 优于独立训练、测试值中 $\\lambda=0.5$ 最优（第 721 页）；分类实验 $\\lambda=1.0$ 时成员正确集交集 113 对独立训练 146，但简单平均的测试误差与独立训练相近，winner-take-all 才明显改善（第 723–724 页）。"
method: "CELS：共享训练过程中同时更新全部成员，损失为成员均方误差加 λ 倍相关惩罚；无噪声用式 (10)、有噪声用式 (11) 的 $p_i$"
baseline: "独立 BP 训练（$\\lambda=0$）、Rosen 的去相关网络、mixtures-of-experts；回归任务与 Australian credit card 分类任务"
aliases:
  - NCL
  - CELS
  - LiuYao1999
related:
  - "[[1995-Krogh-神经网络集成歧义分解]]"
  - "[[2017-Lakshminarayanan-深度集成预测不确定性]]"
  - "[[2019-Fort-深度集成的损失面视角]]"
---

# 同时训练集成中的负相关神经网络（NCL 正源）

> Liu & Yao，IEEE Trans. SMC—Part B 29(6):716–725，1999 年 12 月，10 个物理页。

## 一句话

这篇论文把「成员要负相关」从一句经验口号落成一个可直接优化的惩罚项：每个成员的损失里加 $\lambda p_i$，$p_i$ 是自身偏差与其余成员偏差之和的乘积；成员在**同一次训练**里互相看见彼此的误差，从而被推向负相关，而不是先独立训练再平均。

## 题录与原件

- **Crossref**（`query.bibliographic` 检索题名）返回：DOI `10.1109/3477.809027`，
  题名 *Simultaneous training of negatively correlated neural networks in an ensemble*，
  作者 Yong Liu、Xin Yao，容器 *IEEE Transactions on Systems, Man and Cybernetics,
  Part B (Cybernetics)*，卷 29、期 6、页 716–725，1999 年。
- **Semantic Scholar** 同一 DOI 返回 `externalIds.DBLP = journals/tsmc/LiuY99`，
  可用于与 DBLP 记录键对齐；**OpenAlex** 返回 `volume=29, issue=6,
  first_page=716, last_page=725`，与 Crossref 一致。
- **修正原假设**：出处不是 Part A，而是 **Part B (Cybernetics)**。
  正文引用必须写 Part B，卷期页 29(6):716–725。
- 开放副本：Semantic Scholar 指向作者主页
  `http://www.cs.bham.ac.uk/~xin/papers/published_tsmcB_dec99.pdf`，该 URL 现已跳到
  伯明翰大学新站首页；**Wayback Machine 快照可用**
  （`web.archive.org/web/20200709160753id_/` 同一路径），返回 `application/pdf`，
  10 个物理页。PDF 元数据标题与 Crossref 题录一致，Creator 为 “IEEE Copyright”。
- 本地原件：`raw/papers/methodology/1999-Liu-NegativeCorrelationLearning.pdf`；
  SHA-256 `de7e5d3d74471bb161a672c146a6c80e119eb8a0ca21484408a002bdbe88cfe3`。
- 转换：MinerU `extract -l en --ocr`，10/10 页；式 (8)–(15)、表 I–X 已回 PDF
  物理页视觉复核（第 716–724 页）。

## 动机：为什么成员误差的相关性决定平均的收益

论文开篇把集成平均的收益直接与误差相关性挂钩（物理第 716 页，意译）：

> 当成员无偏时，平均在误差**负相关**时最有效，在误差**不相关**时中等有效，
> 在误差**正相关**时几乎没有收益。

第 717 页用偏差–方差–协方差分解给出形式化：集成期望平方误差 = 偏差平方 +
方差项 + 协方差项（式 7）。其中方差项按 $1/M$ 衰减，**协方差项不会自动衰减**，
除非成员之间的协方差很小（第 717 页）。这解释了为什么「多训几个网络再平均」
不必然带来增益：独立训练的网络在同一数据上学同一个任务，误差往往正相关。

论文对既有路线的批评是：两阶段设计（先独立生成、再组合）切断了组合阶段
对个体训练的反馈，可能产生对集成没有贡献的成员（第 716 页）。CELS 的动机
就是让成员在训练中互相影响、各自specialize 到数据的不同部分。

## 惩罚项：原始定义、符号与梯度

### 1. 成员误差函数（式 8，物理第 718 页）

$$E_i=\frac1N\sum_{n=1}^{N}E_i(n)
=\frac1N\sum_{n=1}^{N}\left[\frac12\left(d(n)-F_i(n)\right)^2+\lambda p_i(n)\right]$$

其中 $N$ 是训练样本数，$F_i(n)$ 是成员 $i$ 在第 $n$ 个样本上的输出，
$p_i$ 是相关惩罚函数，**$0\le\lambda\le1$** 调节惩罚强度（第 718 页正文）。

### 2. 三种 $p_i$ 定义（式 9–11，物理第 718 页）

以回归函数 $g(\mathbf x)=E[d\mid\mathbf x]$ 为参照：

$$p_i(n)=\left(F_i(n)-g(n)\right)\sum_{j\ne i}\left(F_j(n)-g(n)\right)\tag{9}$$

无噪声数据 $g(n)=d(n)$ 时退化为：

$$p_i(n)=\left(F_i(n)-d(n)\right)\sum_{j\ne i}\left(F_j(n)-d(n)\right)\tag{10}$$

有噪声时 $g$ 未知，改用集成输出 $F(n)$：

$$p_i(n)=\left(F_i(n)-F(n)\right)\sum_{j\ne i}\left(F_j(n)-F(n)\right)\tag{11}$$

其中 $F(n)$ 是组合系统在第 $n$ 个样本上的输出。**分类实验使用的正是式 (11)**
（第 723 页，Australian credit card 实验）。

### 3. 符号与作用方向

$p_i$ 是「自己的偏差」乘「其余成员偏差之和」：

- 若成员 $i$ 与其余成员同向偏离目标，$p_i>0$；最小化 $p_i$ 会把成员 $i$ 往
  相反方向推，压低这种同向偏离。
- 若成员 $i$ 与其余成员反向偏离，$p_i<0$；梯度下降会沿同一反向继续推大
  自己的偏离，使 $p_i$ 更负（而不是把成员 $i$ 拉回其余成员的方向）。
- 因此**最小化 $p_i$ 鼓励成员误差负相关**（第 718 页明确写
  “The purpose of minimizing $p_i$ is to negatively correlate each individual's
  error with errors for the rest of the ensemble”）。
- $p_i$ 本身在训练中不保证逐点非负；它不是「多样性奖励」，而是把协方差
  往负方向压的惩罚。

对无噪声形式 (10)，论文给出显式梯度（式 12，第 718 页）：

$$\frac{\partial E_i(n)}{\partial F_i(n)}
=F_i(n)-d(n)+\lambda\sum_{j\ne i}\left(F_j(n)-d(n)\right)$$

梯度下降时，额外项把 $F_i$ 往**其余成员误差之和的反方向**推。论文**没有**给出
式 (11)（用 $F(n)$ 替代 $d$）的显式梯度；实现时需由自动微分处理，或自行推导
$F$ 对 $F_i$ 的依赖项。

### 4. 三个特殊 $\lambda$（式 13–15，物理第 718 页）

把各成员误差相加：

$$E(n)=\sum_i E_i(n)
=\left(\frac12-\lambda\right)\sum_i\left(d-F_i\right)^2
+\lambda\left(\sum_i F_i-Md\right)^2\tag{13}$$

- $\lambda=0$：没有惩罚项，退化为独立 BP 训练（第 718 页）。
- $\lambda=1/2$：$E(n)=\frac12(\sum_i F_i-Md)^2$，即集成误差本身；
  CELS 可视为把集成学习任务分解给各成员（第 718 页，式 14）。
- $\lambda=1$：$\partial E_{\mathrm{ave}}/\partial F_i=\partial E_i/\partial F_i$，
  最小化各成员误差即最小化集成误差（第 718 页，式 15）。

## $\lambda$ 的取值建议与实测

论文没有给跨任务的固定最优值，明确说 **“Choosing a proper value of $\lambda$
is important in CELS, and also problem dependent”**（第 721 页）。实测：

| 设置 | 任务/条件 | $\lambda$ | 结果 | 页码 |
|---|---|---|---|---|
| 无噪声回归，8×5 隐节点 | 合成回归（式 16） | 0–1.0 扫描 | $\lambda\approx0.9$ 时集成 MSE 最小；$\lambda$ 过大时偏差急剧上升 | 第 719 页，表 I |
| 无噪声回归，$A_5/A_{10}/A_{15}$ | 同上 | 0.5 | 三个架构均优于 $\lambda=0$；方差和协方差之和更小 | 第 720 页，表 II |
| 中等噪声 $\sigma^2=0.1$ | 同上 | 0–1.0 扫描 | $0<\lambda\le0.75$ 优于独立训练；测试值中 $\lambda=0.5$ 最优 | 第 721 页，表 III |
| 大噪声 $\sigma^2=0.2$ | 同上 | 0–1.0 扫描 | 同上有噪声条件结论 | 第 722 页，表 IV |
| Mackey–Glass 时间序列 | 20 个成员、6 隐节点 | **1.0** | 泛化优于 EPNet、BP、CC learning | 第 723 页，表 VII–VIII |
| Australian credit card | 4 个成员、10 隐节点 | **1.0** | 简单平均测试误差 0.1337 对独立训练 0.1386；winner-take-all 0.1195 | 第 723–724 页，表 IX |

机制读数（第 719–720 页）：

- 随 $\lambda$ 增大，$E_{var}$ 上升、$E_{cov}$ 下降；无噪声回归中协方差**变为负值**
  （表 I，第 719 页）。
- $A_{10}$ 的 28 个成员间相关系数中，CELS 训练后有 **21 个为负**；
  独立训练**全部为正**（第 720 页，式 25 定义相关系数）。
- CELS 同时降低了集成偏差，并不只是「用方差换协方差」（第 719 页）。

## 分类实验的关键限定

Australian credit card 实验（690 个样本，14 个特征，二分类；第 723 页）使用
式 (11) 的 $p_i$、$\lambda=1.0$、简单平均。论文自己指出一个反直觉结果：

> $\lambda=1.0$ 的简单平均测试误差与独立训练**相近**，表面上与
> 「惩罚项鼓励成员学习数据的不同部分」的主张矛盾（第 723–724 页）。

为核验分工，论文比较了成员**正确响应集**的交集（第 724 页，表 X）：

- CELS($\lambda=1.0$)：四个成员各自正确集 138–147，四者交集 **113**。
- 独立训练：各自 146–149，四者交集 **146**。
- 即 CELS 成员确实在不同样本上正确，只有 113 个样本被四个成员同时做对；
  独立训练几乎完全重合。
- 但简单平均没有把这种分工转成更低的测试误差；**winner-take-all** 才把平均
  测试误差从 0.1386 降到 0.1195（第 723–724 页，表 IX）。

这意味着：**「成员分工」与「简单平均/概率平均的增益」是两件事**。NCL 能制造
分工，不保证均值聚合一定受益；聚合方式与任务指标会改变结论。

## 与本课题「合流」主张的接口

本课题第四章把 NCL 作为「反合流约束」的机制来源：联合训练会让共享主干上的
成员在预测上趋同，NCL 型惩罚用于维持成员分歧（Ā 项）。这篇论文能支撑与不能
支撑的部分必须分开：

**能支撑**

- 「成员误差负相关 → 平均更有效」的动机与偏差–方差–协方差分解（第 716–717 页）。
- 惩罚项的具体形式与符号：$p_i$ 为自身偏差乘其余成员偏差之和，最小化它鼓励
  负相关（第 718 页，式 8–11）。
- 同时训练（而非先独立再组合）可以让成员在训练中互相影响（第 716–718 页）。
- 有噪声时用集成输出 $F$ 替代未知的 $g$（式 11），这正是分类任务的可用形式。

**不能支撑**

- 论文是回归 MSE 与一个小规模分类集，不含年度漂移、共享主干、F1/AUC；
  不能直接推出「NCL 在正例稀缺年提升 F1」。
- 论文的 $\lambda$ 范围是 $[0,1]$，全部实验 $\lambda\le1$；本课题先导预声明
  $\{0.5,2.0\}$，其中 **$\lambda=2.0$ 超出论文范围、无文献依据**，只能登记为
  任务化外推（先导文档已自述 λ 数值无文献依据，此处补充论文边界）。
- 论文只对式 (10) 给出式 (12) 梯度；本课题用式 (11) 形式
  $p_i=(s_i-\bar s)\sum_{j\ne i}(s_j-\bar s)$，梯度需自行推导/自动微分，
  不能把式 (12) 直接当成实现依据。
- 论文分类实验的输出是 1-of-$m$ 编码、简单平均；本课题是 sigmoid 分数、
  概率平均。NCL 分工在该输出形式下是否出现，需由 S1（pairwise 不一致率）
  实测，不能引用表 X 代替。
- 分类实验中简单平均未获益、winner-take-all 才获益（第 723–724 页），
  对本课题「评测合同固定为概率平均」是一个直接警示：即使 NCL 抬高了分歧，
  也未必转化为均值聚合的 F1 增益。

## 证据等级

- 题录：Crossref + Semantic Scholar（DBLP 键）+ OpenAlex 三方一致，**已核实**。
- 全文：作者主页副本的 Wayback 快照，10 页完整，**本地全文已入库**。
- 公式与数字：式 (8)–(15)、表 I–X 已回物理页视觉复核；OCR 转换稿仅作检索辅助。
