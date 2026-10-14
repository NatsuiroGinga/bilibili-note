---
schema: paper-note-search/v1
title: "HYDRA: Proactive Android Malware Drift Adaptation via Hierarchical Graph Contrastive Learning"
title_zh: "HYDRA：基于分层图对比学习的主动式 Android 恶意软件漂移适应"
authors: [Han Chen, Lu Qin, Hanchen Wang, Wenjie Zhang, Hongmei Chen, Ying Zhang]
year: 2026
date: 2026-10-14
journal: "ACM CCS 2026（SIGSAC Conference on Computer and Communications Security，2026-11，作者版含完整附录）"
doi: "10.1145/3830454.3832684"
arxiv_id: "2609.26352"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2026-Chen-HYDRA-Proactive-Android-Malware-Drift-Adaptation.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 图神经网络
  - 对比学习
  - 域适应
  - 伪标签
  - 类型/论文
tasks: [Android恶意软件二分类, 时间漂移适应, 类间漂移（留出家族）]
datasets: [HiGraph, Drebin]
methods: [分层图（FCG+CFG）, 跨域 InfoNCE 对比损失, 源预训练 + 目标伪标签联合适应, 增量 warm-start]
metrics: [F1, Accuracy, FPR, FNR, 标注预算]
key_finding:
  - "HYDRA 把应用建模为『FCG 节点内嵌 CFG』的分层图，用跨域对比损失（而非对抗训练）对齐源/目标分布，在时间一致协议下同时降 FNR 与 FPR。"
  - "它把主动式（proactive）域适应从『单层 CFG + 对抗』推进到『分层图 + 对比』，并在留出家族设置下以 10 个标注样本达到 F1 94.37%。"
method: "CFG 级均值聚合 → FCG 级 GIN → 跨域 InfoNCE（正集=同类真/伪标签，负集=异类）+ 源与已标注目标上的 CE；伪标签样本不进 CE 以隔离噪声"
baseline: "SVM、MLP、TRANS、CADE、HCC、DREAM（主动学习）；ADDA（域适应）；Cold/Warm-start"
aliases:
  - HYDRA
  - Chen2026-HYDRA
related:
  - "[[2024-He-Dream解释性检测与漂移适应]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
  - "[[2026-Kamol-McNdroid多模态长期漂移基准]]"
---

# HYDRA：分层图对比学习的主动式漂移适应

> 页码锚点：标题与摘要位于 PDF 物理第 1 页；本文其余引用按 MinerU 保留的章节号（§1–§6）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2026-Chen-HYDRA-Proactive-Android-Malware-Drift-Adaptation.pdf`）。取得版本为作者版（含完整附录），会议版见 ACM CCS '26，DOI `10.1145/3830454.3832684`。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | HiGraph（AndroZoo 2012–2022 大尺度数据，499,981 应用，Table 1）+ Drebin 留出子集（8 家族，3,317 样本）；2022–2025 放宽标签（VT≥4）补充评估；**未使用 LAMDA** |
| 特征表示 | **分层图**：函数级 CFG（11 维基本块指令统计）+ 应用级 FCG（GIN 编码）；对照变体 HYDRA† 用 Drebin 静态特征（MLP） |
| 平台 | Android |
| 监督设定 | 源域已标注 + 目标域**少量预算标注**（主实验月度 50/100/200/400；留出实验 10–500）+ 大量无标签目标样本的伪标签（§3.3、§4.2） |
| 是否有固定 FPR 工作点 | **无**。报告 F1/Accuracy/FPR/FNR 逐预算与逐家族，未设固定 FPR 运行点 |
| 评价指标 | F1、Accuracy、FPR、FNR（作者强调 FNR 因其运维重要性） |
| 报告的主结果数字 | Table 2（Task A，预算 100）：HYDRA FNR `37.60`、FPR `0.67`、F1 `95.00`（对比 HCC FNR 38.92）；Table 2（Task B，预算 400）F1 `96.38`；§4.3：以 50 样本达到 DREAM 用 400 样本的 FNR 水平，**减少 87.5% 标注**；Table 8 留出：Drebin 预算 10 时 F1 `94.37`、FNR `6.12`、FPR `5.05` |
| 与 LAMDA 本课题的关系 | **仅对照**（图表示 + 域适应的 Android 漂移适应；无 LAMDA 结果）+ **部件来源**（跨域对比对齐、伪标签仅用于对比不进 CE 的噪声隔离设计） |

## 一、论文原结论（带章节号）

- **核心洞见**（§1、Figure 1）：尽管表面持续演化，恶意家族的核心行为常保持稳定（如勒索软件的「文件发现→加密→通知」），据此主张用**分层图**（FCG 高层、CFG 低层）捕获「行为本质」。
- **方法**（§3.2–§3.3）：CFG 级用单步消息传递 + 均值池化得函数嵌入（式 1–2）；FCG 级用 GIN 得应用表示（式 3–4）；适应阶段用**跨域 InfoNCE 对比损失**（式 6，正集=同类标签或伪标签、负集=异类）配以只在源与已标注目标上计算的分类损失（式 7），总损失 `L_total = L_contrast + α·L_cls`（式 5）。作者强调把伪标签样本**排除出 CE** 可隔离伪标签噪声（§3.3）。
- **主动 vs 反应**（§2.2）：把 CADE/Transcend/Dream/HCC 归为「反应式」（检测到漂移才补救），HYDRA 为「主动式」（持续对齐分布以防退化）。
- **时间一致协议**（§4.1、§4.2）：Task A（训 2012，测 2013–2015）、Task B（训 2016，测 2017–2022）；每月用上一个月数据适应、下一个月评估，所有基线同一协议。恶意:良性约 1:9。
- **主结果**（§4.3、Table 2、Table 3）：增量（Incremental）变体在所有预算与任务上 F1 最高、FNR 最低；增量相较每月重载（Adapt）与静态显著更好（预算 100、2015 年 F1 94.06% vs 88.75% / 86.57%），作者归因于避免灾难性遗忘。以 50 预算达到 DREAM 用 400 预算的 FNR（87.5% 标注节省）。
- **策略 vs 表示**（§4.3）：即使用 Drebin 静态特征的 HYDRA†（无分层图）也常超基线，说明适应策略本身有增益；但换成图特征后 FNR 进一步大幅下降（Task A 47.95→38.72）。
- **留出家族（类间漂移）**（§4.6、Table 8）：Drebin 留出实验预算 10 时 F1 94.37%（冷启动 73.71%/68.10%），FNR 6.12%（相对最佳基线 8.10% 降 24.4%）；HiGraph 预算 500 时 F1 97.08%、FPR 1.86%。
- **CFG 退化稳健性**（§4.5、Table 6）：把 CFG 节点特征随机置零 0–50%，F1 仅从 0.948 降到 0.907，作者称 FCG 级编码器补偿了丢失的 intra-procedural 信号。
- **消融**（§4.7、Table 9）：全分层（94.37%）优于仅 FCG（92.72%）与仅 CFG（84.08%，且 FPR 高达 14.44%）；GIN>GAT>GCN。
- **自述威胁**（§5）：静态图构建对混淆脆弱、伪标签连续适应有投毒风险，二者均列为开放问题。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】HYDRA 的「伪标签样本只进对比损失、不进 CE」是一种**噪声隔离**设计，可对齐 LAMDA 关心的「低质量伪标签不能污染分类头」；但它是启发式，作者未给出该设计的独立消融。
- 【推论】HYDRA 与本工作树关心的「静态特征 vs 结构特征」问题直接相关：其 Table 9 显示 CFG-only 的 FPR 高达 14.44%，提示「结构表示层次不匹配会显著放大误报」，可作为 LAMDA 静态单模态边界的旁证。
- 【推论】HYDRA 无固定 FPR 工作点，其 FPR 数值只是各预算下的月度均值，**不得**当作 FPR 约束下的工作点读数。

## 三、可迁移机制（借用边界）

- **跨域对比对齐替代对抗训练**：借用边界是它需要「同类标签或伪标签」构造正集，本质仍依赖标签/伪标签质量；无标签的 LAMDA 零标签端不能直接套用（需先有伪标签）。
- **伪标签不进 CE 的噪声隔离**：可借为 C1 伪标签门的部件；边界是该设计只在图表示 + 对比框架内验证，未在静态特征上验证。
- **增量 warm-start（跨月保留权重）**：借用边界是它只说明「保留权重优于每月重载」，不构成对 LAMDA 记忆/回放机制的等价证据。
- **时间一致协议 + 月度滚动**：可直接借为 LAMDA 的评价协议模板。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「HYDRA 在 LAMDA 上达到某指标」。
- 无固定 FPR 工作点，**不得**把其 FPR 数值当作 FPR 约束下的读数。
- 87.5% 标注节省是相对 DREAM 在其预算曲线上的位置，**不得**当作绝对或跨方法的通用节省率。
- 「分层图捕获漂移不变行为」是**假设**（§3.1 明确称 hypothesis），论文用扰动实验与 t-SNE 佐证但未证明因果；**不得**写成已证实结论。
- CFG 退化实验用「随机置零」模拟混淆，作者自称是上界代理，**不得**当作真实混淆下的性能。

## 五、待验证假设

- 假设 A：在 LAMDA 的静态特征上，「伪标签只进对比、不进 CE」是否降低误报？**最小验证**：LAMDA 上跑「伪标签进 CE」vs「伪标签仅进对比」两臂，比较 ΔFPR。
- 假设 B：HYDRA 的策略增益（HYDRA† vs 基线）在 LAMDA 的静态特征上是否复现？**最小验证**：用 LAMDA 静态特征复现 HYDRA 的适应流水线（不含图）。

## 文献信息

- DOI：https://doi.org/10.1145/3830454.3832684
- 数据集：HiGraph（arXiv 2509.02113）
- 反应式对照：[[2024-He-Dream解释性检测与漂移适应]]
