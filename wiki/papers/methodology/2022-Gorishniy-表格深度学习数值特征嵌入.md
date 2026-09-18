---
title: "On Embeddings for Numerical Features in Tabular Deep Learning"
authors: [Yury Gorishniy, Ivan Rubachev, Artem Babenko]
year: 2022
date: 2026-08-28
journal: "36th Conference on Neural Information Processing Systems (NeurIPS 2022)（第1页页脚标注）；PDF 头部标注 arXiv:2203.05556v4 [cs.LG]，2023年10月26日修订版，共21页"
source_pdf: "[[raw/papers/methodology/2022-Gorishniy-On-Embeddings-Numerical-Features-Tabular.pdf]]"
sha256: "22b97677fec340fc9f95275c9501a8ad5e2fb01a82c0ed829aeb44d33163a0d8"
arxiv_id: "2203.05556v4"
tags:
  - 表格数据
  - 特征嵌入
  - 数值特征
  - 深度学习
  - FT-Transformer
  - 分段线性编码
  - 类型/论文
key_finding: "在11个偏向GBDT友好的表格数据集上，为数值特征设计分段线性编码(PLE)或可训练周期性(Periodic)嵌入后，MLP等简单骨干经嵌入改造可追平甚至反超Transformer与CatBoost/XGBoost集成的平均排名（第8页，表6：MLP-PLR平均排名3.0±2.4，优于CatBoost 3.6±2.9与XGBoost 4.6±2.7）。"
method: "先提出通用数值特征嵌入框架——每个数值特征独立映射为向量、嵌入之间互不混合——再给出两种具体实现：基于分箱的分段线性编码(PLE，分位数分箱或目标感知分箱)与可训练系数的周期性(Periodic/Fourier)激活嵌入；将两类嵌入分别套到MLP、ResNet、Transformer三类骨干上，并与CatBoost、XGBoost集成对比"
baseline: "MLP、ResNet、Transformer(即FT-Transformer)配合Linear/ReLU简单嵌入(L/LR/LRLR)及AutoDis(Guo et al. 2021)的对照嵌入；CatBoost与XGBoost三模型集成作为GBDT基线"
aliases:
  - On Embeddings for Numerical Features
  - Gorishniy2022-数值特征嵌入
  - PLE-Periodic嵌入论文
  - NumEmbed
related:
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
  - "[[2025-Gorishniy-TabM参数高效集成]]"
  - "[[2024-Gorishniy-TabR检索增强表格网络]]"
---

# 表格深度学习中数值特征的嵌入方法

> Gorishniy, Rubachev, Babenko，NeurIPS 2022 · arXiv:2203.05556v4 · 21 页

## 一句话

论文主张"数值特征怎样从标量映射为向量"是表格深度学习里被低估的自由度，提出分段线性编码(PLE)与可训练周期性(Periodic)两类逐特征独立的嵌入方案，证明它们能让 MLP、ResNet、Transformer 三种骨干同时获益，且部分场景下把 MLP 的平均排名从落后 GBDT 拉到反超 GBDT；但全文只研究"已有数值列换表示"，不涉及新增派生特征或时序聚合。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：On Embeddings for Numerical Features in Tabular Deep Learning
- 作者：Yury Gorishniy（Yandex）、Ivan Rubachev（HSE, Yandex）、Artem Babenko（Yandex），第 1 页
- arXiv：2203.05556v4 [cs.LG]，2023 年 10 月 26 日修订版（第 1 页竖排标记）；页脚标注 NeurIPS 2022 正式录用（第 1 页）
- DOI：未在原件中定位（本 PDF 为 arXiv v4 修订版 + NeurIPS 2022 camera-ready 页脚标记，未印刷 DOI）
- 原件：`raw/papers/methodology/2022-Gorishniy-On-Embeddings-Numerical-Features-Tabular.pdf`（21 页，`pdfinfo` 核验 PDF 1.5，LaTeX/pdfTeX 生成）
- 代码：<https://github.com/yandex-research/tabular-dl-num-embeddings>（第 1 页摘要末尾）

## 核心方法

- 通用嵌入框架（第 3 页，3.1 节）：对第 i 个数值特征定义 `z_i = f_i(x_i^(num)) ∈ R^{d_i}`，所有特征的嵌入函数**独立计算、互不共享参数、也不混合其他特征**；MLP 类骨干把各 z_i 拼接成一个向量后再输入（第 14 页附录 A，图 2/图 3，式 3），Transformer 类骨干直接把 z_i 当 token 序列输入，不做额外处理。
- 分段线性编码 PLE（第 3–5 页，3.2 节）：把特征值域切成 T 个分箱 `B_1,...,B_T`，落在当前分箱前的坐标记 0、之后的记 1、当前分箱记线性插值 `(x-b_{t-1})/(b_t-b_{t-1})`（式 1，第 4 页）。分箱来源两种：
  - 无监督分位数分箱（3.2.1 节，第 4 页）：按训练集经验分位数切分。
  - 目标感知分箱（3.2.2 节，第 4–5 页）：用单特征决策树递归切分，思路等价于 Kohavi & Sahami 的 C4.5 离散化算法，叶子对应分箱（图 4，第 14 页）。
  - Transformer 骨干需在 PLE 后加一层不共享权重的线性层以补回特征顺序信息（第 4 页），等价于给每个分箱分配一个可训练向量再按 PLE 权重聚合（式子见第 4 页）。
- 周期性激活嵌入 Periodic（第 5 页，3.3 节，式 2）：`f_i(x) = concat[sin(v), cos(v)]`，`v = [2πc_1x,...,2πc_kx]`，`c_i ~ N(0, σ)` 且**可训练**（区别于 Tancik et al. 2020 原版固定系数）；σ 与 k 都需在验证集上调参，作者强调 σ 是重要超参（第 5 页）。
- 简单可微层（3.4 节，第 5 页）：在 PLE/Periodic 之上叠加 Linear/ReLU 组合（记作 L、LR、LRLR）作为增强与对照模块。
- 命名规则 "Backbone-Embedding"（Table 2，第 6 页）：如 MLP-Q（MLP + 分位数 PLE）、Transformer-T-LR（Transformer + 目标感知 PLE + ReLU∘Linear）；"Transformer-L" 等价于原始 FT-Transformer（第 6 页）；对照嵌入 AutoDis 取自 Guo et al. 2021 的 CTR 方案。
- 实验协议（第 16–17 页，附录 E）：11 个公开表格数据集（GE/CH/CA/HO/AD/OT/HI/FB/SA/CO/MI，Table 1 第 5–6 页，Table 11 详情第 15 页），刻意偏向 GBDT 友好任务；每个调优配置跑 15 个随机种子取均值，用 Optuna 的 TPE 贝叶斯搜索调参，测试集不参与调参（第 16–17 页）；每模型再按 15 个种子分三组做集成对比（第 17 页）。

## 关键数字（含页码/表号）

- 数据集规模（Table 1，第 5–6 页；Table 11，第 15 页）：共 11 个数据集，样本量 9,873–1,200,192，数值特征数 6–200。
- 简单嵌入对 MLP 的增益（Table 3，第 6 页）：MLP-LR 相对 MLP，CA 数据集 RMSE 从 0.495 降到 0.471，HO 从 3.204 降到 3.084。
- PLE 对 Transformer 的增益（Table 4，第 7 页）：Transformer-T-LR 相对 Transformer-L，AD 准确率从 0.858 升到 0.871，CA RMSE 从 0.465 降到 0.454。
- Periodic 对 MLP 的增益（Table 5，第 7 页）：MLP-PLR 相对 MLP，GE 从 0.632 升到 0.674，HO RMSE 从 3.204 降到 3.050。
- DL 与 GBDT 集成的平均排名对比（Table 6，第 8 页）：CatBoost 3.6±2.9，XGBoost 4.6±2.7，MLP 8.5±2.6，MLP-PLR 3.0±2.4，ResNet 6.7±3.3，ResNet-PLR 3.2±1.3，Transformer-L 5.9±2.2，Transformer-PLR 3.9±2.5；作者特别指出 MLP 与 MLP-PLR 之间的排名差距"impressive"（第 8 页）。
- 参数量与训练时间的非线性关系（Table 7，第 9 页，5.1 节）：CH 数据集上 MLP-LR 参数量约为基线 MLP 的 1931.03 倍（约 2000 倍），但训练时间只增加约 1.5 倍。
- 分箱形式的消融（Table 8，第 9 页，5.2 节）：MLP-Q 用分段线性形式时 CH 准确率 0.854，改成 binary（thermometer）形式降到 0.815，改成 one-blob 形式为 0.851——分段线性是必要设计而非任意二值化都可替代。
- 嵌入对 GBDT 无迁移收益（Table 10，第 10 页，5.4 节）：把 Periodic 模块（固定随机系数）套到 XGBoost 上，CA RMSE 由 0.436 变差到 0.441，HO 由 3.160 变差到 3.184，HI 准确率持平 0.724。
- 混合特征反而有害（第 16 页，附录 D.2）：原版 Fourier features（嵌入前先混合多个特征、系数不训练）效果差于原始 MLP，作者据此强调"必须先分别嵌入每个特征、再在骨干中混合"。

## 论文原结论

- 数值特征嵌入是表格深度学习里被低估的自由度，更强的嵌入方案能带来实质性性能提升（摘要，第 1 页；贡献 1，第 2 页）。
- 该增益不是 Transformer 专属：MLP、ResNet 配合合适嵌入后，性能可追平注意力模型（第 2 页贡献 2；第 8 页 4.7 节"after the MLP-like architectures are coupled with embeddings for numerical features, they perform on par with the Transformer-based models"）。
- 在作者选取的、刻意偏向 GBDT 友好的 11 个数据集上，配合嵌入的 DL 模型在大多数"骨干×数据集"组合上能追平 GBDT 集成（第 8 页，4.7 节），作者称这是"就作者所知，首次在 California Housing 与 Adult 数据集上 DL 模型追平 GBDT"（第 8 页）。
- 嵌入带来的参数量开销不必然等比例转化为训练时间开销，MLP/ResNet 加嵌入后仍比 Transformer 骨干快（第 9 页，5.1 节）。
- PLE 表示天然落在 [0,1] 且对平移缩放不变，可部分替代传统标准化/分位数预处理，模型对预处理方式的敏感度降低（第 9–10 页，5.3 节）。
- 该嵌入收益与深度学习的训练特性相关，不是通用特征工程，对 XGBoost 这类树模型没有可迁移收益（第 10 页，5.4 节）。
- 作者自陈局限（第 10 页，第 6 节）：尚未从优化机制层面解释这些嵌入为何有效；本文只研究了"同一嵌入函数套用到所有特征"这一种情形，未测试对不同特征用不同嵌入策略。

## 本课题可迁移机制（LSPR23→LSPR24 加密恶意流量跨年检测）

- PLE 与 Periodic 的具体公式、超参与调参方式（第 4–5 页，式 1、式 2）可直接作为"把逐流数值特征（包大小统计、时长、方向比例等）转成 embedding 再喂进 FT-Transformer 字段级 token / TabM 数值嵌入层"的具体候选实现，而不必自行设计嵌入函数形式。
- 全文检索确认（`grep -n -i "token"`、`"aggregat"`、`"history"`、`"causal"`、`"prefix"` 均已核对）：论文**只对数据集里原本就存在的数值特征换表示**，没有做过"新增派生特征/额外 token"的实验；"token"一词仅在第 2 页相关工作段落出现一次，且是与 NLP 中离散 token 的类比，不涉及新增字段。
- 嵌入方案对 FT-Transformer 与 MLP 的增益均有独立表号支持（Table 4 第 7 页、Table 6 第 8 页），说明"用更好的嵌入替换标量输入"这一机制本身不挑骨干，这支持 M-A 里"用嵌入而非裸标量表示实体因果前缀统计量"这一步的合理性。
- 计算与显存代价：原文只报告了参数量倍数（Table 7，第 9 页）与一个训练时间案例（CH 数据集约 1.5 倍，第 9 页正文），**未报告显存占用或吞吐量的系统数值**；附录 E（第 17 页）提到 GPU/CPU 仅用于 CatBoost/XGBoost 的 task_type 配置，与本文自身 DL 模型的显存代价无关。本课题若采用 PLE/Periodic 风格嵌入实体因果前缀统计量，需要自行测量显存与吞吐量，不能援引本文数字。

## 与 M-A（因果前缀统计量作为额外字段 token）的差量

- 论文做了什么：为**已存在**的数值特征设计更好的标量→向量映射，逐特征独立嵌入、不与其他特征混合，然后拼进 MLP 或作为 token 喂进 Transformer 骨干（第 3 页 3.1 节，第 14 页附录 A 图 2/图 3）。
- 论文没做什么（逐条）：
  1. 没有把"新增的统计量/聚合特征"作为独立 token 加入模型——全部实验的特征列数在原始数据集定义内固定不变（Table 1/11），是"换表示"而非"加列"，没有任何"新增派生特征"的消融。
  2. 没有涉及时序、因果前缀或"到当前样本为止的历史聚合"概念——11 个数据集全部是 i.i.d. 表格任务（Table 1，第 5–6 页），正文未讨论时间维度或实体级历史统计。
  3. 没有做"新增 token 数量变化对模型的影响"这类消融——token/维度变化只来自换嵌入函数后单个特征输出维度 d_i 的变化，token 总数始终等于原始特征列数。
  4. 附录 D.2（第 16 页）唯一涉及"混合"的实验是反例：把多个特征在嵌入前混合（原版 Fourier features）效果变差，进一步说明论文的立场是"每个已有特征独立编码"，而非"引入跨特征/跨时间的聚合统计作为新 token"。
- 结论：本文是"数值特征怎么嵌入"的先例，不是"要不要新增字段/token"的先例。M-A 提出的"实体因果前缀统计量作为额外字段 token"是本文完全没有触及的设计维度；二者可以互补——M-A 新增的统计量列本身仍可以套用本文的 PLE/Periodic 方案做嵌入——但不能引用本文证明 M-A"新增 token"这一步本身有效。

## 不可直接声称的内容

- 不能声称本文验证过"新增聚合统计特征作为额外 token"有效——全文没有该实验（已用 `rg`/`grep` 核实无相关表述）。
- 不能援引本文支持时序或流式场景的结论——11 个数据集全部 i.i.d.，无时间维度（Table 1，第 5–6 页；附录 C，第 15 页）。
- 不能把 Table 6（第 8 页）"MLP-PLR 平均排名超过 CatBoost/XGBoost"当作"深度学习全面超过 GBDT"的证据——作者明确说明该基准本就偏向 GBDT 友好任务，且比较未计入 DL 训练与推理效率成本（第 7–8 页，4.7 节："we focus only on the best metric values without taking efficiency into account"；"compared to GBDT models, efficiency can still be an issue"，第 8 页）。
- 不能引用本文的具体显存占用数字——原文未报告，只报告了参数量倍数与一个训练时间案例。
- 不能把"Periodic 嵌入对 XGBoost 无效"（Table 10，第 10 页）泛化成"该类嵌入机制对所有非深度模型都无效"——作者只测试了 XGBoost 一种树模型、一种嵌入方案（Periodic）、三个数据集（CA/HO/HI）。

## 疑问/待验证

- 论文没有给出 PLE/Periodic 起效的优化机制解释，作者自己列为未来工作（第 10 页，第 6 节）；若要论证"为何该嵌入对本课题实体级 AP 有效"，需要本课题自建证据，不能援引本文的因果解释。
- 论文只测试了"同一嵌入函数套用到所有数值特征"，未测试"部分特征加嵌入、部分不加"或"新增列用专门嵌入"的混合策略（第 10 页，第 6 节自陈局限）；这对应 M-A 中"因果前缀统计量列是否该用与原始特征相同的 PLE/Periodic 配置"这一问题，需本课题单独消融。
- σ（Periodic 频率初始化标准差）与分箱数 T 都是数据集相关的调参项（第 5 页，3.3 节；附录 D.1 图 5 显示分箱数存在最优值而非越多越好），迁移到加密流量特征时需要重新在验证集上搜索，不能照搬本文任何数据集上的具体取值。
- 目标感知分箱（PLE target-aware，3.2.2 节，第 4–5 页）依赖单特征决策树，在本课题高度不平衡的正类分布下是否会产生退化分箱（例如全部样本落入同一叶子）未经验证。

## 可引用的逐字原文（≤15 词）

- "embeddings for all features are computed independently of each other"（第 3 页，3.1 节）

## 证据记录

- 来源类型：完整论文（21 页，`pdfinfo` 核验 PDF 1.5、LaTeX/pdfTeX 生成，sha256 已现场核验；按页码标记的纯文本逐页核对）
- 支持：数值特征嵌入（PLE/Periodic）对 MLP/ResNet/Transformer 三类骨干均有稳定增益，部分场景下追平或反超 GBDT 集成（Table 6，第 8 页）
- 限制：仅覆盖 i.i.d. 表格分类/回归任务，未涉及新增特征/token、时序、实体历史聚合；未报告显存与吞吐量的系统数值
- 论断强度：有支持（数值特征嵌入方案本身对表格深度学习骨干的增益）/ 推论（迁移到本课题"实体因果前缀统计量作为额外 token"的 M-A 机制）

## 文献信息

- arXiv：<https://arxiv.org/abs/2203.05556>
- 代码：<https://github.com/yandex-research/tabular-dl-num-embeddings>
- 会议：36th Conference on Neural Information Processing Systems (NeurIPS 2022)
