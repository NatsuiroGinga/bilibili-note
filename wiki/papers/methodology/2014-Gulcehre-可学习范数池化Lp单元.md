---
title: "Learned-Norm Pooling for Deep Feedforward and Recurrent Neural Networks"
authors: [Caglar Gulcehre, Kyunghyun Cho, Razvan Pascanu, Yoshua Bengio]
year: 2014
date: 2026-08-13
journal: "ECML PKDD 2014（原件为 arXiv:1311.1780v7，2014 年 9 月 2 日版，17 页；PDF 内未印会议卷期页码）"
source_pdf: "[[raw/papers/methodology/multiple-instance/2014-Gulcehre-Learned-Norm-Pooling-ECMLPKDD.pdf]]"
sha256: "78be80b3efeb98d442921ba5f7f71a8f33fd0285f17732a1664942da74015ff9"
tags:
  - 池化算子
  - 表示学习
  - 激活函数
  - 多示例聚合
  - 类型/论文
key_finding: "把池化算子统一写成可学习阶数的归一化 Lp 范数，p=1 退化为平均池化、p=2 为均方根池化、p→∞ 为最大池化；学到的 p 在不同数据集上分布差异显著（MNIST 均值 3.44、TFD 2.04、Pentomino 5.81，表 1，第 12 页），把 p 固定为 2 会使 TFD 测试误差变差到 0.21（第 12 页）。"
method: "提出 Lp 单元 u_j = ((1/N)Σ|a_i − c_i|^p)^(1/p)，用 1+log(1+e^ρ) 重参数化保证 p≥1，用反向传播同时学习权重、中心 c 与阶数 p"
baseline: "maxout、rectifier（ReLU）、logistic sigmoid、固定 p=2 的 L2 单元"
aliases:
  - Gulcehre2014-LearnedNormPooling
  - Lp unit
  - Learned-Norm Pooling
related:
  - "[[2016-Bartos-优化不变表示检测未见恶意软件变种]]"
  - "[[2012-Bilge-DISCLOSURE大规模NetFlow僵尸网络控制服务器检测]]"
---

# 可学习范数池化：平均池化与最大池化是同一族的两端

> Gulcehre, Cho, Pascanu, Bengio, 2014, ECML PKDD（arXiv:1311.1780v7）· 17 页

## 一句话

平均池化、均方根池化、最大池化和 maxout 都是归一化 Lp 范数在 p=1、2、∞ 时的特例；作者把 p 变成可反向传播学习的参数，并用实验证明最优的 p 分布随数据集变化、且同一模型内各单元的 p 也应各不相同。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Learned-Norm Pooling for Deep Feedforward and Recurrent Neural Networks
- 单位：Département d'Informatique et de Recherche Opérationelle, Université de Montréal；Bengio 标注为 CIFAR Fellow（第 1 页）
- arXiv（第 1 页左侧竖排标记）：arXiv:1311.1780v7 [cs.NE]，2 Sep 2014
- DOI：未在原件中定位（PDF 内无 Springer DOI 行与会议卷期页码，会议归属来自文件名与外部著录）
- 原件：`raw/papers/methodology/multiple-instance/2014-Gulcehre-Learned-Norm-Pooling-ECMLPKDD.pdf`

## 核心方法

- Lp 单元定义（式 (3)，第 3 页）：`u_j([a_1,…,a_N]) = ((1/N) Σ_i |a_i − c_i|^{p_j})^{1/p_j}`，其中 `a_i = w_i^T x`，中心 `c_i` 与阶数 `p_j` 都是可学习参数。
- 约束处理（第 4 页）：0<p<1 时三角不等式不成立、不再是范数，故用 `p_j = 1 + log(1 + e^{ρ_j})` 重参数化，学习 ρ 而非 p 本身。
- 与既有算子的关系（第 5 页，3.2 节）：p=1 时化为 `(1/N)Σ|a_i|`，若再约束 a_i≥0 就是平均池化；p=2 时是均方根池化；p→∞ 时 `lim u_j = max{|a_1|,…,|a_N|}`，若 a_i 非负则正好是 maxout 单元；N=2 时是 ReLU 与绝对值单元的推广。
- 分组方式（第 4 页）：把下层激活线性投影成集合 A，再等分成互不重叠的组，每组喂给一个 Lp 单元，即每个 Lp 单元拥有自己私有的一组滤波器。
- 几何解释（第 6–7 页，第 4 节）：每个 Lp 单元在由 `{w_1,…,w_N}` 张成的子空间上定义 Lp 度量，反投影回输入空间是一个超椭圆（p≥1 时保持凸），因此单个单元就能给出弯曲边界，而 ReLU/maxout 只能给分段线性边界。
- 应用到 RNN（第 10–11 页，第 5 节）：在深度转移 RNN（DT-RNN）中，`h_t = g(W^T f(U^T h_{t-1} + V^T x_t))`，外层 g 用饱和的 tanh 保证稳定，内层 f 换成 Lp 单元层，从而在不引发激活爆炸的前提下使用非饱和单元。

## 关键数字（含页码/表号）

- 学到的阶数分布（表 1，第 12 页）：MNIST 均值 3.44、标准差 0.38；TFD 均值 2.04、标准差 0.22；Pentomino 均值 5.81、标准差 1.56。三者初始化时 p 都在 3 附近（第 12 页正文），训练后分布显著分化，Pentomino 甚至呈双峰（图 5，第 10 页）。
- 固定 p 的代价（第 12 页正文）：在 TFD 上把 p 固定为 2 重跑同一实验，测试误差变差为 0.21。
- 泛化误差（表 2，第 13 页）：Lp 在 MNIST 0.97%（此前最好 0.94%）、TFD 20.75%（此前 21.29%）、Pentomino 31.85%（此前 44.6%）、Forest Covertype 2.83%（此前 2.78%）。
  - 注意原件正文与表 2 存在不一致：第 13 页正文写 Pentomino 错误率 31.38%，表 2 写 31.85%；正文还写 Forest Covertype 的此前最好为 3.13%（manifold tangent classifier），而表 2 的 “Previous” 列写 2.78% 并在脚注 4 说明该数字来自 maxout MLP。引用时须注明取自哪一处。
- MNIST 与 TFD 的绝对精度（第 13 页正文）：MNIST 测试准确率 99.03%，对比 maxout 的 99.06%；TFD 识别率 79.25%，对比当前最好的 82.4%（后者使用了大量无标签样本做预训练）。
- 阶数估计的稳定性（表 3，第 14 页）：TFD 五折交叉验证下各折学到的 p 均值为 2.00、2.00、2.01、2.02、2.00，标准差为 10^-4 量级；MNIST 上五次随机初始化的 p 均值为 2.16，均值间标准差仅 0.028。
- 表示效率实验（图 4，第 9 页；说明见第 8 页）：在具有非平稳曲率的二分类合成任务（5000 个样本）上，Lp 单元只用 3 个单元（6 个滤波器）就在全部十次随机运行中达到零训练误差；两个 L2 单元十次全部失败，而两个 Lp 单元至少成功一次；四个 rectifier 单元的边界仍有 64 个错分，Lp 模型为 0。
- RNN 结果（表 4，第 15 页）：复调音乐预测的测试负对数概率，Lp 版 DOT-RNN 在 Nottingam 2.95、JSB 7.92、Muse 6.59，均优于同结构 sigmoid 版（3.22 / 8.44 / 6.97）与此前常规 RNN 最好结果（3.09 / 8.01 / 6.75）。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 给本课题的聚合算子提供了统一的理论框架：本课题当前使用的因果前缀均值 `ctx = cumsum(h)/cumsum(mask)` 正是 p=1 的归一化 Lp 池化（第 5 页，3.2 节）；实体级聚合若改用最大值就是 p→∞。因此“均值聚合 vs 最大值聚合 vs 广义均值聚合”不是三种方法，而是同一族上的三个点，可以用一个可学习的 p 把它们连起来。
- 提供了一个可证伪的最小实验设计：在本课题的实体级聚合层把固定均值替换为可学习 p 的归一化 Lp 池化，比较 AP 与 DR@4%FPR；论文表 1（第 12 页）显示最优 p 随数据集变化很大，这正是“不该硬编码为均值”的直接依据。但论文没有做任何安全流量实验，该迁移属于待验证假设。
- 与“简单聚合胜过复杂序列模型”的关系是间接的：论文证明的是池化算子的形式选择本身有显著影响（固定 p=2 在 TFD 上劣于学习 p），并没有比较池化与循环状态。不能用它支持“RWKV-7 状态递归应当被池化取代”。
- 用于 RNN 的方式值得注意（第 10–11 页）：作者把非饱和的 Lp 层放在饱和 tanh 的内层，以避免深度循环中的激活爆炸。本课题若在序列模型中引入 Lp 聚合，需要类似的稳定性安排。

## 局限（不可直接声称的内容）

- 全部实验都是图像、合成二维数据与复调音乐，没有网络流量、类别极不平衡、跨年度分布漂移或安全任务的证据。
- 表 2 的“Previous”列与正文数字不一致（Pentomino 31.85% vs 31.38%；Forest Covertype 此前最好 2.78% vs 3.13%），且 MNIST/Forest Covertype 上 Lp 并未真正超过既有最好结果，只是“可比”。不能声称 Lp 单元普遍更强。
- 作者对 RNN 结论明确保留：正文承认还需要更多研究才能对 Lp 单元在循环网络中的收益下确定结论（第 14 页）。
- 论文未讨论 p 的学习在极不平衡数据或小正类样本下的稳定性；表 3 显示 TFD 上各折都收敛到 2.00 附近，说明在某些数据上“学习 p”与“固定 p=2”几乎等价，收益并不总存在。
- 该单元是表示层组件，不涉及决策层聚合或多示例包级标签，不能直接当作多示例学习方法引用。

## 可引用的逐字原文（≤15 词）

- “it is beneficial to estimate the order p of the Lp norm”（第 2 页）
- “the optimal orders of Lp units vary across datasets”（第 11 页，6.1 节，声明 1）

## 证据记录

- 来源类型：完整论文（17 页全文，`pdftotext -layout` 抽取并逐页核对；抽取时 poppler 报 “xref num 189 not found”，已重建，正文与表格完整可读）
- 支持：平均/RMS/最大池化是归一化 Lp 范数的特例；最优阶数随数据集显著变化；可学习 p 在低维非平稳曲率任务上表示效率更高
- 限制：无安全流量、无分布漂移、无不平衡实验；部分数字正文与表格不一致；RNN 结论作者自陈需进一步验证
- 论断强度：有支持（池化算子的统一形式与阶数可学习性）/ 待验证假设（迁移到本课题实体级聚合层）

## 文献信息

- arXiv：<https://arxiv.org/abs/1311.1780>（原件为 v7，2014-09-02）
- DOI：未在原件中定位
