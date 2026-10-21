---
title: "Neural Network Ensembles, Cross Validation, and Active Learning"
authors: [Anders Krogh, Jesper Vedelsby]
year: 1995
date: 2026-10-21
journal: "Advances in Neural Information Processing Systems 7（NIPS 1994 会议，论文集常引作 1995）"
source_pdf: "[[raw/papers/methodology/1995-Krogh-神经网络集成歧义分解.pdf]]"
sha256: "0bc7ab6c6cd2d92309fab02464934114020151ff501e8c3d808131ba995389bf"
tags:
  - 集成学习
  - 歧义分解
  - 交叉验证
  - 主动学习
  - 平方损失
  - 类型/论文
key_finding: "对平方损失回归集成，集成误差可精确分解为成员加权平均误差减去加权平均歧义：$E=\\bar E-\\bar A$（式 10，物理第 3 页）；歧义是成员预测相对集成均值的加权方差，可仅用未标注输入估计，因此集成相对平均成员的增益恰好等于歧义，且均匀权重下 $E\\le\\frac1N\\sum_\\alpha E^\\alpha$（式 11，物理第 3 页）。"
method: "加权平均集成；定义歧义为成员输出相对集成均值的加权方差；推导偏差—方差式分解；用交叉验证集制造歧义；用未标注数据估计最优权重；以歧义做 query-by-committee 式主动学习"
baseline: "无监督对照；实验为方波回归上的交叉验证、权重优化与主动/被动学习对比"
aliases:
  - Krogh1995-Ambiguity
  - AmbiguityDecomposition
related:
  - "[[2017-Lakshminarayanan-深度集成预测不确定性]]"
  - "[[2020-Wen-BatchEnsemble高效集成与终身学习]]"
---

# 神经网络集成、交叉验证与主动学习

> Krogh & Vedelsby，NIPS 7，8 个物理页（印刷页 231–238）。

## 一句话

这篇论文给出集成学习中最干净的统计恒等式：在平方损失回归中，集成误差等于成员加权平均误差减去加权平均歧义，因此集成相对平均成员的收益**恰好**是成员之间的 disagreement；它也是「集成增益＝平均歧义项」这一说法的正源。

## 题录与原件

- 官方 proceedings 页：
  <https://papers.nips.cc/paper_files/paper/1994/hash/b8c37e33defde51cf91e1e03e51657da-Abstract.html>。
- 题名 *Neural Network Ensembles, Cross Validation, and Active Learning*；
  作者 Anders Krogh、Jesper Vedelsby；
  官方 `citation_journal_title` 为 *Advances in Neural Information Processing Systems*，
  `citation_volume=7`，`citation_publication_date=1994`。
- **年份口径**：官方页面目录与元数据写 1994（NIPS 7 会议年），通行引用与本次任务采用 **1995**（论文集出版年）。本笔记的 `year` 字段取 1995，题录节保留 1994 官方字段；引用时不要在同一处混写两种年份。
- 官方 PDF：<https://proceedings.neurips.cc/paper_files/paper/1994/file/b8c37e33defde51cf91e1e03e51657da-Paper.pdf>。
- 本地原件：`raw/papers/methodology/1995-Krogh-神经网络集成歧义分解.pdf`，8 个物理页；
  SHA-256 `0bc7ab6c6cd2d92309fab02464934114020151ff501e8c3d808131ba995389bf`。
- 转换：MinerU `extract -l en`，转换稿 `/tmp/krogh-extract/1995-Krogh-神经网络集成歧义分解.md`；
  式 (1)–(15) 已回到 PDF 物理页逐页视觉复核（第 2、3、5、6 页）。

## 设定与歧义分解（核心）

论文的语境是**实值函数回归**：从 $p(x)$ 抽样的样本 $(x^\mu,y^\mu)$，$y^\mu=f(x^\mu)$；集成含 $N$ 个网络，网络 $\alpha$ 的输出为 $V^\alpha(x)$（物理第 2 页，印刷 232）。

### 1. 集成输出与歧义

加权集成输出（式 1，物理第 2 页）：

$$\overline{V}(x)=\sum_\alpha w_\alpha V^\alpha(x).$$

权重满足 $w_\alpha\ge 0$、$\sum_\alpha w_\alpha=1$；论文强调权重和为 1 对后续结果至关重要（物理第 2 页）。

单个成员的歧义与集成歧义（式 2，物理第 2 页）：

$$a^\alpha(x)=\left(V^\alpha(x)-\overline{V}(x)\right)^2,\qquad
\overline{a}(x)=\sum_\alpha w_\alpha a^\alpha(x)=\sum_\alpha w_\alpha\left(V^\alpha(x)-\overline{V}(x)\right)^2.$$

$\overline{a}(x)$ 就是成员输出相对加权均值的加权方差，度量成员在输入 $x$ 上的 disagreement（物理第 2 页）。

成员与集成的平方误差（式 3–4，物理第 2 页）：

$$\epsilon^\alpha(x)=\left(f(x)-V^\alpha(x)\right)^2,\qquad
e(x)=\left(f(x)-\overline{V}(x)\right)^2.$$

### 2. 逐点恒等式

在式 (2) 中加减 $f(x)$，利用权重和为 1，得到（式 5–6，物理第 2 页）：

$$\overline{a}(x)=\sum_\alpha w_\alpha\epsilon^\alpha(x)-e(x)
\quad\Longleftrightarrow\quad
e(x)=\overline{\epsilon}(x)-\overline{a}(x),$$

其中 $\overline{\epsilon}(x)=\sum_\alpha w_\alpha\epsilon^\alpha(x)$ 是成员误差的加权平均。

### 3. 对输入分布取平均：论文的主结果

定义（式 7–9，物理第 3 页，印刷 233）：

$$E^\alpha=\int \mathrm{d}x\,p(x)\epsilon^\alpha(x),\qquad
A^\alpha=\int \mathrm{d}x\,p(x)a^\alpha(x),\qquad
E=\int \mathrm{d}x\,p(x)e(x).$$

于是得到**集成误差分解**（式 10，物理第 3 页）：

$$\boxed{E=\overline{E}-\overline{A}},$$

其中 $\overline{E}=\sum_\alpha w_\alpha E^\alpha$ 是成员泛化误差的加权平均，$\overline{A}=\sum_\alpha w_\alpha A^\alpha$ 是集成歧义（物理第 3 页）。

论文的解读（物理第 3 页）：

- 第一项只依赖各成员的泛化误差；第二项包含**成员之间的全部相关性**。
- $\overline{A}$ 可以**完全用未标注输入**估计，不需要目标函数 $f$ 的真值；这是它可用于模型选择与主动学习的原因。
- 偏差—方差权衡：若集成强偏置，成员函数相似、歧义小，集成误差接近成员平均误差；若方差大，歧义高，集成误差可低于成员平均误差。
- 由此立即得到集成误差不大于成员加权平均误差；均匀权重时（式 11，物理第 3 页）：

$$E\le \frac{1}{N}\sum_\alpha E^\alpha.$$

**严格性边界**：式 (10) 是平方损失下的代数恒等式，不是有限样本泛化界；式 (11) 的等号只在歧义为零（成员在所有输入上一致）时成立。它说明的是「固定成员下集成误差与歧义的关系」，不说明「增加成员一定降低测试误差」——后者还取决于成员误差与相关性如何随 $N$ 变化。

## 交叉验证集成：论文自己的实验并不支持强主张

论文提出用交叉验证集制造成员差异：每个网络留出 $K$ 个样本，使各成员训练集尽量不同，同时用留出样本估计 $E^\alpha$（物理第 3–5 页）。

但作者对实验结果的表述非常克制（物理第 5 页，印刷 235）：

- 在 Figure 2 展示的设置中，$K=40$ 与 $K=0$ 的泛化误差相同，"although not lower"。
- 作者明确写："we have done many experiments, and depending on the experimental setup the curve can take on almost any form, sometimes the error is larger at zero than at 40 or vice versa."
- 作者进一步写："it is still unclear under which circumstances one can expect a drop in generalization error when using cross-validation in this fashion."

**因此不能把本篇引用为「交叉验证集成稳定提升泛化」的证据**；它提供的是分解与机制，交叉验证的收益在原文中是条件性、混合的。

## 最优权重与主动学习

### 最优权重

权重可通过最小化式 (10) 的未标注估计来求（物理第 5–6 页）。对 $E$ 求导并加入约束，得到最优性条件（式 12，物理第 5 页）：

$$E^\alpha-A^\alpha=E\quad\text{或}\quad w_\alpha=0.$$

定义相关矩阵（式 13，物理第 6 页，印刷 236）：

$$C_{\alpha\beta}=\int \mathrm{d}x\,p(x)V^\alpha(x)V^\beta(x),$$

利用权重和为 1，式 (10) 可改写为（式 14，物理第 6 页）：

$$E=\sum_\alpha w_\alpha E^\alpha+\sum_{\alpha\beta}w_\alpha C_{\alpha\beta}w_\beta-\sum_\alpha w_\alpha C_{\alpha\alpha}.$$

在估计出 $E^\alpha$ 与 $C_{\alpha\beta}$ 后，最优权重可用线性规划或其他优化方法求得；相关矩阵与歧义一样可完全用未标注数据估计（物理第 6 页）。注意 $E^\alpha$ 本身仍需要标签或交叉验证估计；论文也提示可用训练误差或正则化替代（物理第 6 页）。

### 主动学习

由式 (6) 与非负性，立即有（式 15，物理第 6 页）：

$$\overline{\epsilon}(x)\ge \overline{a}(x).$$

即歧义是成员加权平方误差的下界：**歧义大的输入必然平均误差大；但歧义小不必然误差小**（物理第 6 页）。论文据此把「集成歧义最大的输入」作为主动学习查询准则，是 query-by-committee 在连续输出上的推广（物理第 6–7 页）。方波实验显示主动学习曲线优于被动学习且散度更小（Figure 3，物理第 7 页，印刷 237）；这是单一玩具函数的实验，不是通用结论。

## 与第四章「集成统计与隐式正则」家族的关系

- **正源地位**：本篇给出「集成增益＝平均歧义项」的精确形式——在平方损失下，集成相对成员平均的误差下降**恰好**是 $\overline{A}$。第四章若把年度模型组成集成，这个恒等式提供了可计算的分账：成员平均误差、成员间歧义、集成误差三者必须满足 $E=\overline{E}-\overline{A}$，不能把集成收益归因于其他机制而不先扣除歧义项。
- **可测量的诊断量**：在固定成员与固定输入分布下，$\overline{A}$ 可由未标注输入估计（物理第 3 页）。这为「成员是否真的在年度之间产生差异」提供了一个不依赖标签的统计量；但它是**平方损失/回归**意义下的量，不能直接当作 F1 或 AUC 的增益分解。
- **机制边界**：本篇的成员差异来自不同训练集或不同拓扑（物理第 3 页），不涉及深度网络、年度序列、非平稳分布或「成员—年度绑定」。它支持「歧义是集成收益的来源」这一机制陈述，不支持任何具体的年度集成方案。
- **权重优化的启示**：式 (14) 把集成误差写成权重的二次型；如果第四章要学习成员权重，这是一个可引用的经典形式。但其最优性条件式 (12) 依赖 $E^\alpha$ 的可估计性；在只有历史年度、没有目标年度标签的设置下，$E^\alpha$ 不能直接获得，必须另设协议。
- **与 Deep Ensembles 的分工**：本篇回答「为什么集成误差会低于成员平均」，是平方损失下的确定性分解；Deep Ensembles 回答「如何训练概率预测器并用混合方差表达不确定性」，是经验性方法。两者不是同一命题，不能互相替代引用。

## 不能支持的论断

- **不能把 $E=\overline{E}-\overline{A}$ 用到交叉熵、0-1 损失、AUC 或 F1 上**。推导依赖平方误差与实值输出；分类指标没有这个恒等式。若要用 Brier 分数做类似分解，需要另行推导并核验，不能直接引用本篇。
- **不能声称集成一定优于单个成员**。式 (11) 只给出不超过成员平均误差的界；歧义可以为零，成员也可能同时很差。
- **不能声称交叉验证集成稳定提升泛化**。作者自述结果依设置而变，且"still unclear"（物理第 5 页）。
- **不能声称主动学习结论可推广**。实验只有一个方波函数与 5 个网络（物理第 7 页）。
- **不能声称本篇处理了分布移位、年度漂移或深度集成**。全文没有这些设定；成员差异来自训练集/拓扑，不是时间域。
- **不能把「歧义可从未标注数据估计」扩展为「无需任何标签即可选择模型」**。式 (10) 中的 $\overline{E}$ 仍需成员误差估计；歧义项本身不需要标签，但完整目标函数需要。
- **不能声称最优权重在有限样本下可稳定求得**。式 (13)–(14) 的 $C_{\alpha\beta}$ 与 $E^\alpha$ 都是估计量；论文没有给出误差传播或置信区间。

## 证据等级

- **原件级别**：NIPS 7 官方 proceedings PDF，8 个物理页（印刷 231–238）；官方页面元数据核验；SHA-256 已记录。
- **已核验**：式 (1)–(6)（物理第 2 页）、式 (7)–(11)（物理第 3 页）、式 (13)–(15)（物理第 6 页）均已对照 PDF 页面视觉复核；交叉验证实验的保留表述见物理第 5 页；主动学习实验见物理第 7 页。
- **未核验**：论文使用的网络规模、训练细节与随机种子；图中具体误差数值（本笔记只引用作者文字结论，未抄录曲线读数）；正式引用年份的出版元数据争议（官方页面 1994 vs 通行引用 1995）。
- **可支撑**：平方损失下的歧义分解、均匀权重上界、权重优化的二次型、以歧义为主动学习准则的机制。
- **实验待证**：该分解在第四章年度集成、非平稳输入分布与分类指标下的任何具体收益；这些都需要本课题实验，不能由本篇推出。
