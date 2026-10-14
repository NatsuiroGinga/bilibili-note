---
schema: paper-note-search/v1
title: "DRMD: Deep Reinforcement Learning for Malware Detection under Concept Drift"
title_zh: "DRMD：概念漂移下恶意软件检测的深度强化学习"
authors: [Shae McFadden, Myles Foley, Mario D'Onghia, Chris Hicks, Vasilios Mavroudis, Nicola Paoletti, Fabio Pierazzi]
year: 2025
date: 2026-10-14
journal: "AAAI 2026（本文为 AAAI-26 论文的扩展版 arXiv 2508.18839，作者在摘要末自述）"
doi: null
arxiv_id: "2508.18839"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2025-McFadden-DRMD-Deep-Reinforcement-Learning-Malware-Drift.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 强化学习
  - 主动学习
  - 拒绝分类
  - 类型/论文
tasks: [Android恶意软件二分类, 概念漂移适应, 拒绝与主动学习的联合决策]
datasets: [Transcendent, Hypercube]
methods: [单步 MDP（上下文 bandit）, PPO, 奖励塑形（时序/不平衡/拒绝）, 滑动窗口微调]
metrics: [AUT, F1, 拒绝率, 标注预算]
key_finding:
  - "DRMD 把每月恶意软件检测与拒识统一为单步 MDP，用 PPO 学一个同时决定『分类/拒识』的策略，避免 ICMDP 多步转移的伪依赖。"
  - "其价值定位为成本折衷而非每项指标最优：分类-拒识策略平均 AUT 提升 10.90，但在部分设置下仍不如确定性基线，作者强调 RL 的贡献是『学何时更新』而非全面胜出。"
method: "MD-MDP：状态=单样本特征，动作={良性, 恶意, 拒识}，奖励=准确率×时序放大×不平衡放大（拒识另加成本项）；PPO 单步训练，新样本滑窗微调"
baseline: "Drebin(SVM)、DeepDrebin(MLP)、Ramda(VAE+MLP)、SL-DRMD；ICMDP 版 DRMD；NeuralTS/NeuralUCB"
aliases:
  - DRMD
  - McFadden2025-DRMD
related:
  - "[[2026-Sabbah-自监督强化学习漂移维护]]"
  - "[[2026-Berruz-漂移检测触发自适应重训]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
---

# DRMD：概念漂移下恶意软件检测的深度强化学习

> 页码锚点：标题与摘要位于 PDF 物理第 1 页；本文其余引用按 MinerU 保留的章节号（§1–§7 与附录 A–C）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2025-McFadden-DRMD-Deep-Reinforcement-Learning-Malware-Drift.pdf`）。取得版本为 AAAI-26 论文的扩展版 arXiv 预印本。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | Transcendent（Barbero et al.，259,230 APK，2014–2018）+ Hypercube（Chow et al.，159,839 APK，2021–2023）；恶意占比约 10%；**未使用 LAMDA** |
| 特征表示 | 稀疏二值特征向量：Drebin（取信息量前 10,000 维）+ Ramda（379 维） |
| 平台 | Android |
| 监督设定 | 每月主动学习（不确定性采样），预算 0 / 50 / 100 / 200 / 400；外加每月拒识（rejection）；被拒样本供人工审查/标注（§4.1、§5） |
| 是否有固定 FPR 工作点 | **无**。主指标为 F1 的 AUT，另报拒绝率与标注预算；未设固定 FPR 运行点 |
| 评价指标 | Area Under Time（AUT，基于 F1）；标注预算；拒绝率；配对 t 检验显著性 |
| 报告的主结果数字 | 摘要与 §1：分类-仅策略平均 AUT 提升 `8.66`，分类-拒识策略 `10.90`；Table 1：AL=400、Rej=400 时 Hypercube-Drebin AUT 达 `84.66 ± 0.52`（相对最佳基线 `+7.67`）；Table 2：IR 设置平均 ΔBase `16.15`，IRAAL 平均 ΔBase `10.75` |
| 与 LAMDA 本课题的关系 | **仅对照**（RL 驱动的漂移维护；不同协议，无 LAMDA 结果）+ **部件来源**（拒识 + 主动学习的联合决策框架） |

## 一、论文原结论（带章节号）

- **问题重述**（§3）：给出 TESSERACT 的三条时间感知约束（C1 训练早于测试、C2 同一时间窗、C3 恶意占比真实），并用 AUT（式 1，对 F1 轨迹积分）作为时间感知指标。
- **方法核心**（§4.1、§4.2）：把检测建模为**单步 MDP/上下文 bandit**——每个 episode 只处理一个样本，状态即样本特征，动作 `{a_gw, a_mw, a_rej}`。奖励由准确率奖励 `R_acc`（式 2）、恶意类上采样 `R_imb`（式 3，`1/σ̂`）、时序放大 `R_tmp`（式 4）与拒识奖励 `R_rej`（式 5，含平坦成本 `R_cost`）相乘/组合而成。作者明确指出该设计修正了 ICMDP 把独立样本当序贯依赖的缺陷（§1、§4.1）。
- **训练**（§4.2）：用 PPO（单步改造）训 actor-critic；新样本到达后只对最新样本滑窗微调。
- **主结果**（§6.1、Table 1）：分类-仅策略在无 AL/拒识时平均超最佳基线 `+6.94` AUT；月拒识设置下 16 个设置中 15 个显著提升，平均 ΔBase `15.01`；AL 设置下 16 个中 9 个显著提升，平均 ΔBase `2.52`（作者归因于 AL 的边际收益递减）。MD-MDP 相对 ICMDP 在 100 个设置中 97 个更好（平均 ΔIC `1.94`），相对 DCB（NeuralTS/NeuralUCB）全部 100 个显著更优。
- **分类-拒识策略**（§6.2、Table 2）：引入拒识动作与三种拒识成本；IR 设置平均 ΔBase `16.15`，IRAL `11.60`，IRAAL `10.75`。提高 `R_cost` 会减少拒识数且对 ΔBase 影响很小。
- **消融**（Table 3）：从最简 DRMD 起逐项加回，作者强调「奖励拒识结果」带来最大提升，其次是「整合拒识 + AL」与「滑窗重训」。
- **自述局限/负证据**（§6.1）：明确报告**并非所有设置都占优**——在 Transcendent-Drebin 上部分设置 ΔBase 为负；作者把 RL 的价值定位为「跨设置成本折衷」，不是每项指标最优。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】DRMD 的「RL 不保证全面胜出、只保证成本折衷」与 Sabbah 的自监督+RL 结论方向一致；两篇共同提示：把漂移维护形式化为 RL 时，「学何时更新」的价值需与同动作空间的固定规则严格比较才能成立。
- 【推论】DRMD 的拒识动作在部署期可实时弃权，这与 LAMDA 的「先导段标定 + 部署期决策」思路可衔接，但 DRMD 依赖真实的月度标注预算，与 LAMDA 的零/低标签端不同轴。
- 【推论】DRMD 无固定 FPR 工作点，对 LAMDA 的 FNR@固定FPR 轴**不构成占位读数**；其 AUTO 值也不能作为 LAMDA 基线的直接对照。

## 三、可迁移机制（借用边界）

- **单步 MDP 形式化**：把「单样本分类 + 是否弃权/送审」写成上下文 bandit。借用边界：可作为 C1「每日/每窗口维护动作决策」的形式化先例；但需注意 DRMD 的状态**不含**目标标签泄露（状态是输入特征 + 统计），这点与 Sabbah 不同。
- **奖励塑形**（时序放大 `R_tmp`、不平衡放大 `R_imb`、拒识成本 `R_cost`）：借用边界是这些项需在 LAMDA 的成本结构下重标定，不能照抄常数。
- **AUT 指标 + 时间感知三约束**：可直接作为 LAMDA 时间轴评价的规范（与本文库既有 [[2019-Pendlebury-TESSERACT时空实验偏置与AUT]] 一致）。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「DRMD 在 LAMDA 上达到某指标」。
- 论文自述在部分设置（如 Transcendent-Drebin）**劣于**基线，**不得**把 DRMD 写成「在所有设置均优于基线」。
- 无固定 FPR 工作点，**不得**把其 AUT/F1 当作 FPR 约束下的读数。
- 依赖每月主动学习标注（每个 AL 设置都用了真标签），**不得**声称它是零标签方法。

## 五、待验证假设

- 假设 A：在 LAMDA 上，RL 维护策略相对「同动作空间的固定规则（周期性更新、漂移规则）」是否有非平凡增益？**最小验证**：LAMDA 上实现 {周期更新, 漂移阈值规则, RL} 三臂，比较 AUT 与成本。
- 假设 B：DRMD 的拒识机制在 LAMDA 的固定 FPR 预算下能否降低 FNR？**最小验证**：把拒识动作接到固定 FPR 的阈值决策上，测量 FNR 变化。

## 文献信息

- arXiv：https://arxiv.org/abs/2508.18839
- 代码：https://github.com/s2labres/DRMD
- 时间感知协议来源：[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]
