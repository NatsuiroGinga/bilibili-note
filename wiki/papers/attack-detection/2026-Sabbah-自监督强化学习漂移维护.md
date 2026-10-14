---
schema: paper-note-search/v1
title: "Concept Drift Adaptation Using Self-Supervised and Reinforcement Learning in Android Malware Detection"
title_zh: "Android 恶意软件检测中的自监督与强化学习概念漂移适应"
authors: [Ahmed Sabbah, Mohammed Kharma, Mohammad Alkhanafseh, Samer Zain, Radi Jarrar, David Mohaisen]
year: 2026
date: 2026-10-14
journal: "arXiv 2605.24294v1（2026-05-22，预印本）"
doi: null
arxiv_id: "2605.24294"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 强化学习
  - 自监督学习
  - 模型维护
  - 类型/论文
tasks: [Android恶意软件二分类, 概念漂移维护, 强化学习]
datasets: [Android emulator malware, Android real-device malware]
methods: [自监督掩码重建编码器（冻结）, 潜空间漂移统计（KS/WD）, 轻量适配器, PPO 成本感知维护控制器]
metrics: [AUT, 平衡准确率, 宏F1, 记忆集准确率, 维护成本]
key_finding:
  - "该预印本把漂移维护定义为 PPO 在保持、分类头、适配器、联合更新和重置之间选动作，并用冻结自监督编码器 + 潜空间漂移统计驱动决策。"
  - "它明确假设每个新窗口标签立即可用，并把当前评价子集的 F1/平衡准确率用于状态和奖励；不能直接支持 LAMDA 最终未来测试上的无标签强化学习。"
method: "冻结自监督编码器、潜漂移统计、轻量适配器、PPO 成本感知维护控制器；维护动作空间 {A0 保持, A1 头, A2 适配器, A3 联合, A4 重置+联合}"
baseline: "Frozen-init、Head-Tune、Adapter-Tune、Joint-Tune、Periodic-Joint(2)、Drift-Rule"
aliases:
  - Sabbah2026-SSL-RL
related:
  - "[[2025-McFadden-DRMD强化学习恶意软件漂移]]"
  - "[[2025-Roh-MADCAT自监督测试时适应]]"
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
---

# 自监督表示与强化学习漂移维护

> 页码锚点：标题位于 PDF 物理第 1 页；状态、动作与奖励见第 IV-F 节，结果见表 II（本笔记按 MinerU 保留的章节号引用）。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android.pdf`；同一 PDF 另有副本 `raw/papers/attack-detection/lamda-related/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf`）。取得版本为 arXiv 2605.24294v1 预印本。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | 模拟器与真机两类 Android 恶意软件数据集（2008–2020，年度窗口），静态与动态特征各一组；**未使用 LAMDA**（论文引用 LAMDA 仅作漂移证据，第 II 节 [17]） |
| 特征表示 | 静态特征与动态特征（两套；具体维度与字段未在正文给出） |
| 平台 | Android |
| 监督设定 | **标签可用的周期维护**：初始化前 K=3 个窗口用真标签；每个新窗口按有标签处理，再切成不相交的适应子集与评估子集（第 IV-F、IV-G 节）。**无主动学习标注预算** |
| 是否有固定 FPR 工作点 | **无**。主指标为平衡准确率、宏 F1 的 AUT，加记忆集准确率与累积维护成本 |
| 评价指标 | 当前窗口平衡准确率、当前窗口宏 F1、记忆集平衡准确率、累积维护成本；三者的 AUT；六个种子 |
| 报告的主结果数字 | Table II：real-dynamic 中 RL 平均准确率约 `0.628`，成本约 `3.75`（Periodic-Joint(2) 成本 7.50，Joint-Tune/Drift-Rule 15.00）；real-static 中 RL 平均宏 F1 约 `0.752`；emulator-static 中 RL 约 0.774 准确率、0.719 宏 F1。Periodic-Joint(2) 在 real-dynamic 的宏 F1 约 0.473 高于 RL（第 V 节） |
| 与 LAMDA 本课题的关系 | **仅对照**（RL 维护；标签即时可用，无 LAMDA 结果）+ **部件来源**（冻结自监督编码器 + 潜漂移统计 + 轻量适配器） |

## 一、论文原结论（带章节号）

- **框架三阶段**（第 IV 节）：① 初始化期用前 K 个窗口拟合缩放器并自监督预训练掩码重建编码器，之后**冻结编码器**（第 IV-B、IV-D 节，损失见式 8）；② 每个新窗口在冻结潜空间计算相对上一窗口与初始化参考池的漂移（KS 均值 + Wasserstein 均值，第 IV-E 节）；③ 从第 K+1 个窗口起，PPO 在动作空间 `{A0 保持, A1 只调分类头, A2 只调适配器, A3 联合更新, A4 重置适配器后联合更新}` 中选择（第 IV-F 节）。
- **状态与奖励**（第 IV-F 节）：10 维状态含当前窗口的平衡准确率/宏 F1、记忆集准确率、相对上一窗口与初始化的 KS/WD 漂移、上一动作、模型年龄与上一动作成本；奖励 `R_t = [α·F1_post + (1−α)·BA_post + β·BA_mem + G_t − λ_c·Cost(a_t)]`，漂移**不直接进奖励**，只作为状态。
- **协议与结果**（第 IV-G、V 节、Table II）：所有策略用同一初始化期、冻结编码器、记忆集、适应/评估切分与预算。结论是：无维护（Frozen-Init）在漂移下不足；**没有任何确定性规则在所有设置上最优**；RL 的价值是「跨设置成本折衷 + 状态依赖决策」，而非每项指标最优。real-dynamic 中 RL 平均准确率最高（约 0.628）且成本低（约 3.75），但宏 F1 由 Periodic-Joint(2) 更高（约 0.473）。
- **种子一致性**（第 V 节）：RL 的 AUT 跨六个种子波动较窄（如 emulator-static 准确率 0.769–0.777），作者称比固定规则更不敏感。
- **自述威胁**（第 V-A 节）：① 年度窗口 + K=3 初始化，结论只支持该粒度；② 假设**标签可用维护**，每个新标注窗口再切适应/评估子集，而非完全在线无即时标签适应；③ 固定动作空间与确定性基线，RL 训练 4096 PPO 步；④ 未评估校准、对抗稳健性或延迟反馈。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】Sabbah 与 DRMD 同属 RL 维护路线，但 Sabbah 用「冻结 SSL 编码器 + 轻量适配器」把更新限制在小参数上，DRMD 直接训 PPO 分类/拒识策略；两篇都自述「RL 不全面胜出」，提示 RL 在漂移维护中的价值主张必须靠**同动作空间的固定规则对照**支撑。
- 【推论】Sabbah 的状态与奖励都用当前评价子集的真标签指标，因此**不能**直接在 LAMDA 的零标签未来窗上运行；若迁移，必须先解决「状态在动作时真实可见」。
- 【推论】其潜空间漂移统计（KS/WD）作为「可观测量」与 LAMDA 先导段标定思路可衔接，但该文未对漂移统计做触发/阈值型消融，故不构成漂移检测机制证据。
- 【推论】无固定 FPR 工作点，对 LAMDA 的 FNR@固定FPR 轴**不构成占位读数**。

## 三、可迁移机制（借用边界）

- **冻结自监督编码器 + 轻量适配器**（第 IV-C、IV-D 节）：借用边界是它把「表示稳定」与「下游可调」解耦，可迁移到 LAMDA 的「冻结骨干 + 小适配器维护」；但该设计依赖标签可用，且适配器容量与记忆容量未与 LAMDA 合同对齐。
- **潜空间漂移统计（KS 均值 + WD 均值）**：可借为 LAMDA 的漂移可观测量；边界是它只在冻结潜空间成立（编码器一旦更新即不可比）。
- **系统化维护动作空间 {保持/头/适配器/联合/重置}**：可借为 LAMDA 维护动作的枚举模板；边界是每个动作的成本常数需按 LAMDA 真实开销重标定。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「该框架在 LAMDA 上达到某指标」。
- 论文明确是**标签可用维护**（第 V-A 节），**不得**声称它支持无标签或延迟反馈的在线适应。
- 评价子集参与了状态与奖励构造（第 IV-F 节），**不得**把它当作「用最终测试标签训练策略无泄漏」的先例；它只适用于周期性维护且真标签可用。
- RL 并非所有指标最优（宏 F1 由 Periodic-Joint(2) 更高），**不得**只引用 RL 最好的数字。
- 无固定 FPR 工作点，**不得**把其平衡准确率/宏 F1 当作 FPR 约束下的读数。

## 五、待验证假设

- 假设 A：在 LAMDA 上，若状态不含真标签指标（仅用无标签漂移统计），RL 维护是否仍有增益？**最小验证**：把状态中的 AUC/F1 项替换为无标签漂移统计，重训策略并比较。
- 假设 B：RL 相对「同动作空间的固定规则」在 LAMDA 上是否有非平凡增益？**最小验证**：LAMDA 上跑 {Periodic-Joint(k), Drift-Rule, RL} 三臂，比较 AUT 与成本。

## 文献信息

- arXiv：https://arxiv.org/abs/2605.24294
- 同路线：[[2025-McFadden-DRMD强化学习恶意软件漂移]]（拒识 + RL）、[[2025-Roh-MADCAT自监督测试时适应]]（SSL 适应）
