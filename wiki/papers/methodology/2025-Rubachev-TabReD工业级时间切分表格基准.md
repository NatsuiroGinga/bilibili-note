---
title: "TabReD: Analyzing Pitfalls and Filling the Gaps in Tabular Deep Learning Benchmarks"
authors: [Ivan Rubachev, Nikolay Kartashev, Yury Gorishniy, Artem Babenko]
year: 2025
date: 2026-08-28
journal: "International Conference on Learning Representations 2025（ICLR 2025）；本地原件为 arXiv:2406.19380v4 [cs.LG]，2024 年 10 月 24 日，35 页，首页标注 Preprint"
source_pdf: "[[raw/papers/methodology/2025-Rubachev-TabReD-Tabular-Benchmark-Pitfalls.pdf]]"
sha256: "8aebc851f8e4ebacbb646f1edcacba2718c8f853af3931c748b9040604722f94"
arxiv_id: "2406.19380v4"
tags:
  - 表格数据
  - 时间分布漂移
  - 时间切分评价
  - 特征工程
  - 基准数据集
  - 数据泄漏
  - 类型/论文
key_finding: "作者审查 100 个常用表格数据集，发现 11 个含泄漏、13 个不可溯源或合成、25 个本质非表格，且 53 个含时间漂移的数据集里只有 15 个带时间戳可做时间切分（第 4 页表 1）；据此构建 8 个工业级、全部带时间切分的 TabReD 数据集，重评后 GBDT 与带数值嵌入的 MLP 最强，检索增强模型与长训练/重构辅助目标这两类在学术基准上有效的技术在 TabReD 上不再有效（第 7 页表 3、第 8 页图 1）。"
method: "先人工审查 6 个既有基准共 100 个数据集的泄漏、可溯源性、表格性与时间戳可用性；再从 Kaggle 竞赛与某大型科技公司生产 ML 系统构建 8 个带时间切分的数据集；随后在统一 Optuna 调参、时间切分验证选轮、15 个随机种子的协议下重评 GBDT、MLP 系、FT-Transformer、Trompt、数值嵌入、集成、增强训练配方与检索增强模型"
baseline: "XGBoost、LightGBM、CatBoost、RandomForest、线性模型、MLP、SNN、DCNv2、ResNet、FT-Transformer、MLP-PLR、Trompt、MLP 集成、MLP-PLR 集成、MLP aug.、MLP aug. rec.、TabR、ModernNCA、DeepCORAL、DFR"
aliases:
  - TabReD
  - Rubachev2025-TabReD
  - 工业级时间切分表格基准
related:
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
  - "[[2025-Gorishniy-TabM参数高效集成]]"
  - "[[2024-Gorishniy-TabR检索增强表格网络]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
  - "[[2025-Cai-时间漂移下深度表格方法的极限]]"
---

# TabReD：工业级时间切分表格基准

> Rubachev, Kartashev, Gorishniy, Babenko，ICLR 2025；本地原件 arXiv:2406.19380v4 · 35 页

## 一句话

作者论证学术表格基准缺两样工业现实——**随时间推移的渐进漂移**和**大量工程化聚合特征**——补上这两条之后，近年多数表格深度学习"进步"不再成立，只剩数值嵌入和集成两项能迁移过来。

## 题录

- 题名（第 1 页）：TabReD: Analyzing Pitfalls and Filling the Gaps in Tabular Deep Learning Benchmarks
- arXiv：2406.19380v4 [cs.LG]，2024 年 10 月 24 日（第 1 页左侧竖排）
- 正式出处：ICLR 2025（本地 PDF 是 v4 预印本版式，首页标 "Preprint"，不含 ICLR 版式）
- 原件：`raw/papers/methodology/2025-Rubachev-TabReD-Tabular-Benchmark-Pitfalls.pdf`
- 代码：<https://github.com/yandex-research/tabred>（第 1 页脚注与 arXiv comment）

## 论文原结论

### 一、既有基准的三类问题（第 3–4 页，第 3 节与表 1）

- 审查范围是 6 个既有基准合计 **100 个**唯一分类/回归数据集。
- **泄漏 11 / 100**：eye movements、visualizing soil、Gesture Phase、sulfur、artificial-characters、compass、Bike Sharing Demand、electricity、Facebook Comments Volume、SGEMM GPU kernel performance、Shifts Weather（in-domain 子集）（第 4 页）。
- **不可溯源或合成 13 / 100**；**本质非表格 25 / 100**（如展平的图像）（第 4 页）。
- **时间切分缺位**：排除有问题的数据集后仍有 **53 个**数据集因按时间采集而可能含时间漂移，但只有 **15 个**带可用时间戳（第 4 页）。
- 规模对比（第 4 页表 1，中位数）：Grinsztajn 基准 16,679 样本 / 13 特征；Tabzilla 3,087 / 23；TableShift 840,582 / 23；**TabReD 7,163,150 / 261**。

### 二、TabReD 的构成（第 5 页表 2，第 16–17 页附录 B）

八个数据集：Sberbank Housing（20K / 387 特征）、Homesite Insurance（224K / 296）、Ecom Offers（106K / 119）、HomeCredit Default（381K，全量 1.5M / 696）、Cooking Time（228K，全量 10.6M / 195）、Delivery ETA（224K，全量 6.9M / 225）、Maps Routing（192K，全量 8.8M / 1026）、Weather（605K，全量 6.0M / 98）。

**特征构造方式（第 16–17 页附录 B，对本课题最关键的一段）**：

- Ecom Offers：特征来自"两个月交易历史"（第 16 页）。
- Cooking Time：特征基于订单内容加上**该餐厅与该品牌的历史烹饪时长信息**（第 17 页）。
- Delivery ETA：特征包含骑手可用性、导航数据以及**按不同时间片对历史信息做的各种聚合**（第 17 页）。
- Maps Routing：特征是**该路线的路网图统计量聚合**加路况细节（第 17 页）。

即：TabReD 的入选判据之一就是"特征工程与特征采集尽量贴近工业实践"，Kaggle 侧照搬论坛顶尖方案的特征工程代码，自建侧直接使用生产 ML 系统的实际特征（第 5 页第 4 节判据 (2)）。

### 三、评价协议（第 6 页 5.1 节）

- 默认按时间把每个数据集切成 train / validation / test；**模型按验证集表现选择，调参与早停都用同一验证集**；测试结果对 15 个随机种子聚合并考虑标准差判显著性。
- 沿用 Gorishniy et al. (2024) 的训练、评价与调参设置，DL 用 AdamW，优化 MSE 或二元交叉熵。

### 四、主结果（第 7 页表 3，平均排名）

| 方法 | 平均排名 |
| --- | --- |
| MLP-PLR ens. | 2.4 ± 1.5 |
| XGBoost | 2.9 ± 1.5 |
| LightGBM | 3.1 ± 1.5 |
| CatBoost | 3.4 ± 1.7 |
| MLP-PLR | 3.8 ± 1.4 |
| MLP ens. | 4.1 ± 2.0 |
| **FT-Transformer** | **4.8 ± 1.6** |
| MLP | 5.0 ± 1.8 |
| Trompt | 5.4 ± 2.1 |
| ModernNCA | 5.6 ± 1.6 |
| ResNet | 5.8 ± 2.0 |
| MLP aug. / TabR | 6.0 ± 2.0 / 6.0 ± 2.2 |
| SNN | 6.6 ± 2.0 |
| MLP aug. rec. | 6.8 ± 2.8 |
| DCNv2 | 7.6 ± 2.3 |
| RandomForest | 7.8 ± 2.0 |
| Linear | 8.8 ± 2.7 |

作者的逐条结论（第 7–8 页 5.2 节）：GBDT 与 MLP-PLR 总体最好；数值嵌入与集成两项技术在新场景仍然有效；**FT-Transformer 是深度侧亚军**，但注意力对特征数二次复杂度使它在 TabReD 这种特征多的数据上更慢；SNN、DCNv2、ResNet、Trompt 都不优于 MLP；检索增强（TabR、ModernNCA）表现较差；长预训练与增强类训练配方基本不迁移。

### 五、哪些技术不迁移及作者给的解释（第 8 页 5.3 节与图 1）

TabReD 上相对 MLP 的平均相对变化：MLP aug. **−1.48%**、MLP aug. rec. **−1.98%**、ModernNCA **−1.05%**、TabR **−2.78%**；而 MLP-PLR **+0.61%**、MLP-PLR ens. **+1.28%**、XGBoost **+0.91%**、MLP ens. **+0.67%**（第 8 页图 1 右）。同组技术在 Gorishniy et al. (2024) 基准上则全为正。

作者的假设（第 8 页）：一是 TabReD 特征更多、共线与噪声特征更复杂，影响近邻选择与特征打乱增强；二是检索类方法假设"训练对象对预测测试实例有用"，而渐进时间漂移破坏了这一假设；长训练配方可能同样因隐式记忆训练集难例而受损。

### 六、时间切分 vs 随机切分（第 8–9 页 5.4 节与图 2）

用滑动窗口造三组时间切分与三组同规模随机切分，各 15 个种子。结论：时间切分测试集上分数随初始化的离散度更大；**模型排名与相对差距都会改变**；最显著的是 XGBoost 相对 MLP 的优势在时间切分上缩小（Sberbank Housing、Cooking Time、Delivery ETA、Weather、Ecom Offers、Quote Conversion），作者据此推测 GBDT 对漂移更不稳健、在随机切分上可能利用了时间泄漏。

### 七、集成预测标准差被用作漂移代理（第 13–14 页附录 A.1 与图 3）

作者把 **MLP 集成预测的标准差随时间的曲线**与同期误差曲线并排画，明说 "We use std in ensemble of MLP predictions as a proxy for the distribution shift"（第 14 页图 3 题注，逐字 13 词）。三条观察：部分数据集漂移随时间上升且误差同步上升（Homesite Insurance、Sberbank Housing）；部分呈强季节性（Cooking Time 测试集有特定时段性能骤降）；**也存在漂移增大而指标反而变好的情况**（HomeCredit Default），作者解释为目标变量的方差与不可约噪声本身随时间下降。

### 八、分布漂移稳健方法无效（第 15–16 页附录 A.3 与表 4）

把 DeepCORAL（按时间戳分桶成域）与 DFR（在训练集后段实例上微调 MLP 表示）适配到时间漂移场景后，两者平均排名 1.4 ± 0.7 与 1.4 ± 0.5，均**不优于** MLP 的 1.0 ± 0.0；作者称这与 Gardner et al. (2023)、Kolesnikov (2023) 在其他漂移上的结果一致。

## 本课题可迁移机制

- **时间切分是评价合同，不是可选项**：本课题 LSPR23→LSPR24 跨年协议与该文主张同型；该文提供了"随机切分会改变模型排名"的外部证据，可用于论证本课题不做随机切分的必要性（第 8–9 页 5.4 节）。
- **强基座选择的外部佐证**：在时间漂移＋特征丰富条件下，深度侧最强的是"MLP＋数值嵌入＋集成"，FT-Transformer 次之。本课题实测 FT-Transformer 与 TabM 为最强基座，与该文的方法学排序方向一致，但**该文没有评测 TabM**，不能据此声称 TabM 在 TabReD 条件下的名次。
- **"表示层改造 / 辅助重构目标 / 检索增强"在时间漂移下失效**，是本课题第三章已实测的三类失败（表示层融合有害、辅助目标夺权）的独立同向证据（第 8 页图 1）。
- **集成方差作为漂移代理**已有published用法（第 14 页图 3），可作为 M-C 的机制来源引用；但该文只把它当作**诊断绘图**，没有把它接进任何决策或聚合规则。

## 与 M-A（实体历史字段 token）的差量

| 维度 | TabReD 已做 | M-A 的增量 |
| --- | --- | --- |
| 实体历史聚合量作为特征 | **已做且是常态**：Ecom Offers 用两个月交易历史、Cooking Time 用餐厅与品牌历史时长、Delivery ETA 用多时间片历史聚合（第 16–17 页） | 不构成"首次把历史聚合量用于表格模型"的新颖点，此话不得写进论文 |
| 这些量的进入方式 | 作为**普通数值列**进入模型，与其他列同等对待；论文未区分它们的角色 | M-A 要把它们作为**角色独立的额外 token**进入字段注意力/数值嵌入通道，并显式声明因果前缀边界 |
| 是否做过"加/不加历史聚合特征"的受控消融 | **未做**：TabReD 把工程化特征当作数据集的既定属性，没有拆出历史聚合特征做单独消融 | M-A 的 C00 vs +M-A 双臂正是这个缺口 |
| 因果性 | 论文未讨论历史聚合特征的因果前缀构造与泄漏边界 | M-A 必须显式冻结因果边界（这是本课题的合同要求，不是该文的贡献） |
| 领域 | 电商、金融、配送、导航、气象 | 加密恶意流量的实体（主机/IP）跨年检测 |

**判定**：M-A 在"用实体历史聚合量"这一层**没有新颖性**；可主张的增量只剩三条——(1) 作为独立角色的 token 化放置方式，(2) 在强表格基座上对该类特征做受控消融，(3) 安全域跨年实体级 AP 的评价单元。**且方向证据偏负**：TabReD 的强基座在已含大量历史聚合特征时，仍是"越简单越好"。

## 与 M-B（实体级选择-校准）的差量

- TabReD 的协议**已经**用时间切分验证集做调参与早停（第 6 页 5.1 节），所以"用时间切分验证"不是 M-B 的新颖点。
- 但该文的验证指标与测试指标**同级同类**（AUC-ROC / RMSE，逐样本），没有出现"验证指标与部署指标处于不同聚合单元"的情形。本课题的"逐流代理指标 vs 实体级 AP"这一**指标层级错配**在该文中不存在，是 M-B 可占的空白。
- 该文未做任何校准实验。

## 不可直接声称的内容

- 不能说"TabReD 证明 TabM 在时间漂移下最强"——**TabReD 没有评测 TabM**（第 7 页表 3 无 TabM 行）。
- 不能说"TabReD 证明输入级历史特征有效"——该文没有做该类特征的加减消融。
- 不能把该文的百分比（如 MLP-PLR ens. +1.28%）与本课题实体 AP 的百分点混用：该文是跨数据集的相对百分比变化，本课题是单一数据集的绝对 AP 点。
- 该文测试的是回归 RMSE 与二分类 AUC-ROC，**不含 AP / AUPRC**，也不含任何实体级或群组级指标。

## 疑问 / 待验证

- TabReD 的历史聚合特征是否满足严格因果前缀（不含未来信息）？论文只说"避免泄漏"，未给出逐特征的因果定义（第 5 页判据 (3)）。**待验证**。
- 该文声称检索类方法失效源于"训练对象对测试实例不再有用"，只是假设（第 8 页原文用 "We hypothesize"），未做隔离实验。
- 附录 A.1 的集成方差-误差关系非单调（HomeCredit Default 反例），M-C 若把方差当作方向性信号，必须先在本数据上验证符号一致性。

## 本笔记的核验状态

全文按 `pdftotext -layout` 提取后逐页核读，页码为 PDF 物理页码。表 1、表 2、表 3、表 4 与图 1、图 2、图 3 的数字均回原文核对。
