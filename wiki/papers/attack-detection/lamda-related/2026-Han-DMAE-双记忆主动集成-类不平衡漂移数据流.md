---
schema: paper-note-search/v1
title: "DMAE: dual-memory active ensemble learning for multi-class imbalanced concept-drifting data streams"
title_zh: "DMAE：面向多类不平衡概念漂移数据流的双记忆主动集成学习"
authors: [Meng Han, Yajie Xue, Yikai Li, Cuicui Ma, Jian Ding, Juan Li]
year: 2026
date: 2026-10-15
journal: "Springer（DOI 10.1007/s44443-026-01127-1，2026-04-30 投稿 / 2026-07-21 接收，gold OA）"
doi: "10.1007/s44443-026-01127-1"
arxiv_id: null
evidence_level: "本地全文（MinerU extract）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2026-Han-DMAE-双记忆主动集成-类不平衡漂移数据流.pdf]]"
tags:
  - 数据流学习
  - 概念漂移
  - 主动学习
  - 类不平衡
  - 记忆管理
  - 类型/论文
tasks: [多类不平衡数据流分类, 概念漂移适应, 在线主动学习]
datasets: [15 个合成数据流, 5 个真实不平衡数据流]
methods: [在线集成, ADWIN 漂移检测, BAM²-Lite 变阈值不确定性查询, 标签滑窗, 类级短窗+长期原型双记忆 SDMI-PDSR, PCN-Weight 复合样本加权]
metrics: [Accuracy, Kappa, G-Mean, Recall]
key_finding:
  - "DMAE 把「预算感知的标注获取」「多类不平衡」「混合概念漂移」「集成演化」放进一个统一在线框架（§1 原文：an effective online learner should jointly address drift adaptation, multiclass imbalance, and budget-aware label acquisition within a unified framework）。"
  - "存储侧有界：§局限原文「although the memory sizes and PDSR trial length are bounded」；标注侧受限（labeling rate 变化下鲁棒）；但作者自认「When the labelling budget is extremely small, this estimate may become less stable, especially for rare classes」——极端稀缺情形明确未解决。"
supports: [标注预算+有界记忆+类不平衡+漂移同框架共置的先例存在（流式学习侧）, 记忆维护策略可由漂移强度在线驱动]
cannot_support: [双预算作为联合配置量的优化问题已被形式化, 深度回放/Domain-IL 情形, 恶意软件域读数]
method: "随机标注 + BAM²-Lite 主动标注协作；ADWIN 漂移强度控制双记忆混合比（SDMI）；试用期软替换（PDSR）；PCN-Weight 统一边界难度/不平衡状态/原型关系/时间衰减"
baseline: "十个流式集成基线（在线 bagging 系）"
aliases:
  - DMAE
  - Han2026-DMAE
related:
  - "[[2020-Chrysakis-CBRS不平衡在线持续学习]]"
  - "[[2024-Park-PBR先验无关平衡回放]]"
---

# DMAE：双记忆主动集成学习（多类不平衡漂移流）

> 页码锚点：按 MinerU 保留的章节号与公式号引用（式 17 为不平衡指示 imb_y）。证据等级：本地全文。

## 一、协议与预算（与待核任务逐项对照）

- **标注预算**：受「limited labeling budgets」约束——只有到达实例的一小部分可被标注（§1）；机制是随机标注子过程（为标签滑窗提供近似无偏类分布估计）与主动标注子过程（BAM²-Lite 变阈值，把预算集中到「genuinely ambiguous, minority-relevant regions」）协作；实验在「different labeling rates」下测鲁棒性（摘要）。
- **存储预算**：类级短期样本窗 + 长期原型记忆，局限节明文「memory sizes and PDSR trial length are bounded」；SDMI 按 ADWIN 漂移强度在线设定双记忆混合比——**「存什么」是自适应决策量，但其大小是有界超参，不是与标注预算联合优化的配置量**。
- **类不平衡**：多类、固定与可变不平衡比（贡献 1 原文「fixed and variable multiclass imbalance ratios」）；PCN-Weight 含类配额归一化。
- **协议与域**：传统流式在线集成（在线 bagging），15 合成 + 5 真实流；**非恶意软件、非 LAMDA、非深度回放 CL、非 Domain-IL**。
- **与目标任务的差量**：四要素（标注预算/有界记忆/不平衡/漂移）在同一框架共置，是「部分同构」里最强的一篇——但「标什么」与「存什么」之间没有联合配置结构（预算也不互相牵制），且底座是流式集成而非神经回放。

## 二、对目标任务的可用之处

- 「标签滑窗做近似无偏类分布估计」直接回应「正例稀缺时两个配置量失去作用对象」的估计问题；其局限自述恰是待核任务的病灶所在（预算极小 + 稀有类 → 估计不稳）。
- SDMI/PDSR 说明「存什么」可以由漂移强度在线驱动，可作为目标任务中存储策略层的机制候选来源。

## 三、论文可支持/不可支持

- 可支持：统一框架内共置四要素的先例存在；极端稀缺是公认未解难点（作者自述）。
- 不可支持：双预算联合配置已被形式化研究；恶意软件/LAMDA 域结论。

## 四、入库与 Zotero

- PDF：`raw/papers/attack-detection/lamda-related/2026-Han-DMAE-双记忆主动集成-类不平衡漂移数据流.pdf`（Springer gold OA，直下）。
- 全文转换件：`wiki/papers/attack-detection/lamda-related/2026-Han-DMAE-双记忆主动集成-类不平衡漂移数据流-全文.md`。
- Zotero：本轮未导入。
