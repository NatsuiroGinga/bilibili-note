---
title: "Baseline Needs More Love: On Simple Word-Embedding-Based Models and Associated Pooling Mechanisms"
authors: [Dinghan Shen, Guoyin Wang, Wenlin Wang, Martin Renqiang Min, Qinliang Su, Yizhe Zhang, Chunyuan Li, Ricardo Henao, Lawrence Carin]
year: 2018
date: 2026-08-13
journal: "arXiv:1805.09843v1 [cs.CL]，2018 年 5 月 24 日，13 页（本 PDF 首页未标注 ACL 2018 等正式会议信息）"
source_pdf: "[[raw/papers/methodology/2018-Shen-SWEM-Baseline-Needs-More-Love-Pooling.pdf]]"
sha256: "6e801e9279fbe4826bd22c2bcf45293d0aa3a18cfe79e9f1f77e7279464e55f2"
tags:
  - 简单基线
  - 池化
  - 序列建模
  - 负面结果
  - 评价方法论
  - 类型/论文
key_finding: "无任何组合参数的平均/最大池化（SWEM）在 17 个 NLP 数据集的多数任务上追平或超过 LSTM 与 CNN；Yahoo! Answer 上 SWEM-concat 以 61K 参数取得 73.53% 准确率，高于 LSTM 的 70.84% 与 29 层深度 CNN 的 73.43%（表 2、表 4，第 5 页）。"
method: "把变长文本的组合函数退化为无参数池化：平均池化 SWEM-aver、最大池化 SWEM-max、二者拼接 SWEM-concat、局部窗口平均再全局最大的层级池化 SWEM-hier；与 LSTM/CNN 在同一评价流程下逐点对比，并用词序打乱与子空间训练做机制诊断"
baseline: "LSTM、单层与深层 word CNN（29 层）、fastText、Bag-of-means、DAN"
aliases:
  - SWEM
  - Shen2018-简单词嵌入池化
  - Baseline Needs More Love
related:
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
  - "[[2023-Zeng-Transformer对时序预测是否有效]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
---

# SWEM：无参数池化就能打平 LSTM 与 CNN

> Shen 等，2018，arXiv:1805.09843v1 · 13 页

## 一句话

把句子表示从 LSTM/CNN 退化成"对词向量做平均或取最大"这种零组合参数的池化后，在 17 个数据集上多数任务性能持平甚至更好；作者进一步用词序打乱实验证明，这些任务本来就不依赖词序，只有情感分析类任务真正需要局部顺序，而一个简单的层级池化即可补上。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Baseline Needs More Love: On Simple Word-Embedding-Based Models and Associated Pooling Mechanisms
- arXiv：1805.09843v1 [cs.CL]，2018 年 5 月 24 日（第 1 页左侧竖排标记）
- DOI：未在原件中定位（本 PDF 版本无 DOI 与会议版式标记）
- 原件：`raw/papers/methodology/2018-Shen-SWEM-Baseline-Needs-More-Love-Pooling.pdf`
- 代码：<https://github.com/dinghanshen/SWEM>（摘要，第 1 页）

## 核心方法

- SWEM-aver（式 1，第 3 页）：`z = (1/L) Σ_{i=1..L} v_i`，即对序列内所有词向量按维度取均值，输出维度与词向量相同。
- SWEM-max（式 2，第 3 页）：`z = Max-pooling(v_1, ..., v_L)`，逐维取最大值，等价于让与任务无关的词自动退出表示。
- SWEM-concat（第 4 页）：把 aver 与 max 的结果拼接，理由是二者信息互补。
- SWEM-hier（第 4 页，3.3 节）：先在长度为 n 的局部窗口上做平均池化，再在所有窗口上做全局最大池化，用来在不引入组合参数的前提下保留 n-gram 级空间信息。
- 复杂度对照（表 1，第 4 页）：CNN 组合参数 `n·K·d`、复杂度 `O(n·L·K·d)`、顺序操作 `O(1)`；LSTM 参数 `4·d·(K+d)`、复杂度 `O(L·d² + L·K·d)`、顺序操作 `O(L)`；SWEM 参数 0、复杂度 `O(L·K)`、顺序操作 `O(1)`。
- 统一实验设置（第 4–5 页）：全部模型用 K=300 的 GloVe 初始化，Adam 优化，最终分类器为一层 MLP，学习率、dropout、batch size 均在给定集合内按验证集选择。

## 关键数字（含页码/表号）

- 长文档分类（表 2，第 5 页）：Yahoo! Ans. 上 SWEM-concat=73.53、SWEM-hier=73.48、29 层 Deep CNN=73.43、LSTM=70.84、Large word CNN=70.94；AG News 上 SWEM-concat=92.66 高于 Deep CNN 的 91.27 与 LSTM 的 86.06；DBpedia 上 SWEM-concat=98.57 对 LSTM 98.55。
- 情感任务是例外（表 2，第 5 页）：Yelp P. 上 Deep CNN=95.72、Large word CNN=95.11 高于 SWEM-aver 的 93.59；但引入层级池化后 SWEM-hier=95.81 反超；Yelp F. 上 SWEM-hier=63.79 接近 Deep CNN 的 64.26，远高于 SWEM-aver 的 60.66。
- 参数与速度（表 4，第 5 页，Yahoo! Answer）：CNN 541K 参数 171s，LSTM 1.8M 参数 598s，SWEM 61K 参数 63s。
- 句对匹配（表 5，第 6 页）：SNLI 上 SWEM-max=83.8 高于 CNN 82.1 与 LSTM 80.6；MultiNLI matched 上 SWEM-max=68.2 高于 LSTM 的 66.9；Quora 上 SWEM-concat=83.03 高于 LSTM 82.58；WikiQA 是唯一 CNN/LSTM 占优的匹配数据集（LSTM MAP=0.6820 对 SWEM-max 0.6613）。作者称 SWEM-max 用 120K 参数达到 SNLI 83.8%（第 7 页）。
- 词序消融（表 6，第 7 页）：把训练集内每句词序随机打乱后，LSTM 在 Yahoo 上 72.78→72.89、SNLI 上 78.02→77.68 基本不变，但 Yelp P. 上 95.11→93.49 明显下降；作者指出打乱后的 LSTM 结果已非常接近 SWEM。
- 短句任务反例（表 8，第 9 页）：MR 上 CNN=81.5 高于 SWEM-concat 78.2；SST-1 上 Constituency Tree-LSTM=51.0 高于 SWEM-concat 46.1；作者据此判断短序列更依赖词序。
- 线性分类头（第 9 页，5.2 节）：把非线性 MLP 换成线性分类器，Yahoo! Ans. 仅从 73.53% 降到 73.18%，Yelp P. 从 93.76% 降到 93.66%。
- 中文实验（第 9 页，5.3 节）：Sogou 语料上 SWEM-concat=91.3%，SWEM-hier（窗口 5）=96.2%，高于文中引用的 CNN 95.6% 与 LSTM 95.2%。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 直接支持"简单池化胜过复杂序列模型"的先例。本课题中因果前缀均值 `ctx = cumsum(h)/cumsum(mask)` 得到 AP 0.1848–0.2879，而完整 RWKV-7 状态递归更差，这与 SWEM 的核心观察同构：当任务信号不依赖精细时序顺序时，参数化的循环组合函数反而带来优化难度与过拟合，而无参数聚合已经足够。引用本文可为"把有界历史聚合器作为主力表示"提供已发表的方法论依据。
- 提供了可直接照搬的证伪实验设计：表 6 的"训练集打乱词序、测试集保持原序"是一个廉价且判据明确的诊断，可迁移为"打乱同一流内包/同一实体内流的时间顺序后重训，观察 AP 是否下降"。若本课题打乱后 AP 基本不变，则说明序列模型的额外容量确实无处可用，可作为放弃复杂递归的实验证据。
- 层级池化提示了一条中间路线：完全无序聚合与完整递归之间，还存在"局部窗口平均 + 全局最大"这种既保留局部顺序又零组合参数的结构，可作为本课题的候选消融项。
- 参数与速度对照（表 4）支持在同等预算下优先把简单聚合调到最优，再谈复杂模型；这与仓库既有的"共同预算强基线"纪律一致。

## 局限（不可直接声称的内容）

- 全部实验在 NLP 监督分类与句对匹配上完成，没有网络流量、类别极不平衡、AP/DR@FPR 这类稀有正类指标，也没有跨年度分布漂移的证据。
- 论文没有做任何分布漂移下的退化测量：训练与测试始终同分布，因此不能用来支持本课题"零样本跨年度迁移"的具体结论。
- 论文没有实体级或分组聚合的对照，与本课题"实体级（2-IP 无向对）聚合把 AP 提到 0.5233–0.5475"的现象不构成同类证据，只能作为"决策层聚合有效"的松散类比，属推论。
- 作者自陈短句任务与序列标注（CoNLL2000 分块、CoNLL2003 NER，结果在补充材料）上 LSTM/CNN 仍优于 SWEM（第 8 页），且小数据集结果对正则化非常敏感。

## 可引用的逐字原文（≤15 词）

- "SWEMs exhibit comparable or even superior performance in the majority of cases considered"（摘要，第 1 页）
- "Simple pooling operations are surprisingly effective at representing longer documents"（第 9 页，第 6 节结论要点）

## 证据记录

- 来源类型：完整论文（13 页，`pdftotext -layout` 抽取后逐页核对；`file` 判定为 PDF 1.5，sha256 已记录）
- 支持：零参数池化在多数文本任务上追平或超过 LSTM/CNN；词序打乱实验可判定任务是否真的需要顺序建模
- 限制：无分布漂移、无安全数据、无不平衡指标、无实体级聚合证据
- 论断强度：有支持（简单聚合优于复杂序列模型的先例）/ 推论（迁移到加密流量跨年度检测）

## 文献信息

- arXiv：<https://arxiv.org/abs/1805.09843>
- 代码：<https://github.com/dinghanshen/SWEM>
