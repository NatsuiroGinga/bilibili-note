---
schema: paper-note-search/v1
title: "SEED: Semi-supervised Continual MalwarE Detection for Tackling ConcEpt Drift on a BuDget"
title_zh: "SEED：预算约束下对抗概念漂移的半监督持续恶意软件检测"
authors: [Suresh Kumar Amalapuram, Bikraj Shresta, Siva Ram Murthy Chebiyyam, Bheemarjuna Reddy Tamma, Sumohana Channappayya]
year: 2026
date: 2026-10-14
journal: "ACM Transactions on AI Security and Privacy（作者标注 Accepted，June 2026）；取得版本为 arXiv 2605.24903 预印本"
doi: null
arxiv_id: "2605.24903"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2026-Amalapuram-SEED-Semi-Supervised-Continual-Malware-Drift-Budget.pdf]]"
tags:
  - Android恶意软件
  - Windows恶意软件
  - 概念漂移
  - 持续学习
  - 半监督学习
  - 主动学习
  - 标注预算
  - 固定FPR
  - 类型/论文
tasks: [Android恶意软件二分类, Windows PE 二分类, 域增量持续学习, 开集未知家族检测]
datasets: [BODMAS, AndroZoo, APIGraph]
methods: [SVD 基向量表示空间, 最适标注样本匹配（改 BCE 正对学习）, 梯度投影记忆 GPM, 延迟缓冲更新, 双组平衡主动采样]
metrics: [PR-AUC, AUT, TPR@固定FPR, 各类 AUT]
key_finding:
  - "SEED 不依赖对比损失：把每个无标签样本投影到已有标注样本的 SVD 基向量空间、找最相似标注样本并拉近表示，配合 GPM 与延迟缓冲，在 20% 标注下超过 HCL* 达 40%（BODMAS）/14%（AndroZoo）。"
  - "它是本轮 8 篇中唯一在固定 FPR 工作点（10⁻¹/10⁻²/10⁻³）评估 TPR 的一篇，因此同时占据『标签预算轴』与『固定 FPR 工作点轴』。"
method: "两阶段 SSCL：seen 任务用 CE + 改 BCE 正对学习 + GPM 正交投影 + 回放；unseen 任务用基向量空间余弦距离双组平衡主动采样，再按 seen 流程训练；延迟缓冲缓解标签噪声"
baseline: "EWC、A-GEM、CBRS、MIR（全监督 CL）；CADE、HCL、HCL*（对比学习）"
aliases:
  - SEED
  - Amalapuram2026-SEED
related:
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
  - "[[2023-Amalapuram-ECBRS-PAPA网络入侵持续学习]]"
  - "[[2026-Kamol-McNdroid多模态长期漂移基准]]"
---

# SEED：预算约束下的半监督持续恶意软件检测

> 页码锚点：标题与摘要位于 PDF 物理第 1 页，页眉标注「Accepted to ACM Transactions on AI Security and Privacy (June 2026)」；本文其余引用按 MinerU 保留的章节号（§1–§12）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2026-Amalapuram-SEED-Semi-Supervised-Continual-Malware-Drift-Budget.pdf`）。取得版本为 arXiv 2605.24903 预印本。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | BODMAS（Windows PE，2019-08 至 2020-09）+ AndroZoo（Android，2019–2021，DREBIN 特征）+ APIGraph（Android，2012–2018，DREBIN 特征）；**未使用 LAMDA**（虽属同一作者组） |
| 特征表示 | 稀疏二值特征向量：DREBIN 特征（APIGraph 1,159 维、AndroZoo 16,978 维）；BODMAS 2,381 维 PE 特征 |
| 平台 | Android + Windows |
| 监督设定 | 半监督持续学习：**seen 任务用 20% 标注数据**（Table 3 口径，随机选），unseen 任务**全无标签**，由月度标注预算（50/100/150/200/250）由分析师标注少量样本（§5.2、§6.4） |
| 是否有固定 FPR 工作点 | **有**。§6.8「Operating-Point Evaluation at Fixed False Positive Rates」在 **FPR = 10⁻¹、10⁻²、10⁻³** 下报告 TPR 随任务序列的演化（Figure 9–11） |
| 评价指标 | 基指标 PR-AUC（式 13 展开为 AUT）；分类别 AUT（seen/unseen/overall 的 benign 与 malware）；TPR@固定 FPR |
| 报告的主结果数字 | Table 3（20% 标注）：SEED unseen-AUT(A) `0.810±0.027`（BODMAS）/ `0.855±0.018`（AndroZoo）/ `0.930±0.002`（APIGraph）；HCL* 对应 `0.613/0.780`（预印本摘要作 0.795→0.613、0.879→0.780）；摘要：相对 HCL* 平均 AUT 提升 40%（BODMAS）、14%（AndroZoo） |
| 与 LAMDA 本课题的关系 | **直接近邻**（预算半监督持续学习，与 C1 标签预算轴正面重合；且含固定 FPR 工作点）+ **部件来源**（SVD 基向量空间匹配、GPM、延迟缓冲） |

## 一、论文原结论（带章节号）

- **动机与关键发现**（§1、Fig. 1）：对比学习方法（HCL）在**部分标注**下显著退化——BODMAS 从 0.795 降到 0.613、AndroZoo 从 0.879 降到 0.780（AUT）；作者据此主张不依赖对比损失的半监督持续学习。
- **seen 任务训练**（§5.1）：对每个无标签样本，用 SVD 从历史标注样本的潜表示中取基向量构造表示空间（累计奇异值比 95% 阈值，式 3），把样本投影进去，用余弦距离 + 自适应软阈值找「最适标注样本」（式 4–5，`τ_max' = τ_max · exp(−rβ)`），再用**改写的 BCE 正对学习**（式 6–9）拉近两者表示；总损失 `L = L_sup + L_bce`（式 10）。表示用 **GPM 梯度投影**正交于历史任务梯度（式 11–12）。
- **unseen 任务训练**（§5.2）：对完全无标签任务，用潜空间到良性/恶意两组的平均余弦距离排序，**每月预算一半给良性组、一半给恶意组**（作者发现纯「最远」准则会偏向良性类）；随后按 seen 流程训练。
- **延迟缓冲**（§5.3）：不立即把新标注样本写入回放缓冲，而是延迟 1/3/11 个月后再纳入，以缓解标签噪声在回放中的传播。
- **主结果**（§6.2、Table 3）：20% 标注下 SEED 在所有指标上不劣于或优于 HCL 与 HCL*；AUT 提升见摘要。SVD 消融（Table 1）：无 SVD 时 BODMAS unseen-AUT(A) 0.752，有 SVD 时 0.810。
- **固定 FPR 工作点**（§6.8、Fig. 9–11）：在 FPR = 10⁻¹/10⁻²/10⁻³ 下比较 SEED 与 CADE/HCL/HCL* 的 TPR 轨迹；SEED 在更严格工作点下保持更高的 TPR 且更平稳，HCL 波动更大。
- **标签噪声**（§6.7、Table 11–13）：10%–80% 噪声比下，直接用翻转标签训练会急剧退化（如 APIGraph 5% 标注时 unseen-AUT(A) 从 0.84 降到 0.08）；加延迟缓冲（+1/+3/+11）后稳定在约 0.86–0.90。
- **假阳性敏感性**（§6.6、Table 10）：`τ_max` 最佳范围 0.01–0.05（对应余弦相似度约 95%–99%）；阈值增大则被拒样本减少、unseen-AUT(A) 略降（BODMAS 0.810→0.798）。
- **自述局限**（§8）：方法依赖 seen 任务的**部分标注**（非零标签）；对比基线、动作空间固定；在「跨类」而非仅「跨时间」上的泛化有限。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】SEED 是本轮 8 篇中**唯一**同时覆盖「标签预算轴」与「固定 FPR 工作点轴」的工作，因此对 C1 的两个轴都构成直接占位；主代理做候选排序时须把它排在最高优先核对档。
- 【推论】SEED 与 CITADEL 同属一个作者组（Amalapuram 同时出现在两篇），路线相邻但机制不同：CITADEL 用一致性正则 + 对比损失 + 主动采样，SEED 明确**弃用对比损失**改为 SVD 基向量匹配。二者可作为「对比 vs 非对比」的配对近邻。
- 【推论】SEED 的固定 FPR 评估是「按任务序列报告 TPR」，属于描述性工作点比较，**不是**带有限样本证书的条件阈值构造（与 TRANSCENDENT/保形路线不同轴），故对 LAMDA 的分面证书主张**不构成占位**。

## 三、可迁移机制（借用边界）

- **SVD 基向量表示空间 + 最适标注样本匹配**：借用边界是它需要一个「历史标注样本池」（buffer memory），与 LAMDA 的记忆容量合同需对齐；且匹配依赖余弦距离在连续潜空间成立。
- **延迟缓冲更新**（§5.3）：可直接借为「抑制伪标签/噪声标签传播」的部件；边界是延迟时长（1/3/11 月）是在 VirusTotal 标签动态性文献上调的，LAMDA 需重标定。
- **固定 FPR 工作点评估**（§6.8）：可直接借为 LAMDA 评价协议的一个模板——在 FPR=10⁻¹/10⁻²/10⁻³ 下报告 TPR 轨迹；但需注意 SEED 未提供有限样本保证，只是经验工作点。
- **双组平衡主动采样**（§5.2）：借用边界是它假设已知类别数（闭集），与 LAMDA 的开集风险不同。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「SEED 在 LAMDA 上达到某指标」。
- 固定 FPR 评估是**经验工作点比较**，不含有限样本证书或条件覆盖率保证，**不得**把它当作「分面证书」或「给定 FPR 的统计上界」。
- seen 任务需要 20% 标注，**不得**把它写成零标签方法。
- 摘要给出的 40% / 14% 是相对 HCL*（部分标注版对比学习）的提升，**不得**当作相对强基线或绝对提升。

## 五、待验证假设

- 假设 A：在 LAMDA 上，SEED 的「SVD 基向量匹配」相对「对比损失（HCL 系）」是否同样在部分标注下更稳？**最小验证**：LAMDA 上 20% 标注下跑 SEED 式匹配 vs 对比损失两臂，比较 unseen-AUT。
- 假设 B：SEED 的固定 FPR 工作点曲线在 LAMDA 上是否平坦（不随时间大幅下滑）？**最小验证**：LAMDA 冻结静态模型，在 FPR=10⁻² 下测各年 TPR 轨迹。

## 文献信息

- arXiv：https://arxiv.org/abs/2605.24903
- 同作者组近邻：[[2025-Haque-CITADEL半监督主动漂移适应]]、[[2023-Amalapuram-ECBRS-PAPA网络入侵持续学习]]
