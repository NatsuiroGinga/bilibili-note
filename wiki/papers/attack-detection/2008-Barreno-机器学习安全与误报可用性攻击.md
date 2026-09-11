---
title: "The Security of Machine Learning（对抗机器学习的威胁模型与可用性攻击分类学）"
authors: [Marco Barreno, Blaine Nelson, Anthony D. Joseph, J. D. Tygar]
year: 2008
date: 2026-09-11
journal: "UCB/EECS-2008-43 技术报告（加州大学伯克利分校 EECS，2008-04，26 页）；会议初步版见 ASIACCS'06（ACM，2006-03）；期刊扩展版见 Machine Learning 81(2):121–148, 2010"
source_pdf: "[[raw/papers/attack-detection/2008-Barreno-Security-of-Machine-Learning.pdf]]"
tags:
  - 对抗机器学习
  - 威胁模型
  - 可用性攻击
  - 误报
  - 入侵检测
  - 类型/论文
key_finding: "给出对抗机器学习系统的**三轴攻击分类学**：影响面（**Causative** 影响训练 / **Exploratory** 只利用已有弱点）、安全目标（**Integrity** 攻击瞄准**漏报 false negatives** / **Availability** 攻击瞄准**误报 false positives**）、特异性（**Targeted** / **Indiscriminate**）（p.5、p.8）。其中 **Availability 攻击**的正式表述是「**造成拒绝服务，通常通过诱发误报**」，即让学习器把良性实例判为恶意，从而由学习器自身拒绝正常输入（p.8）。这把「攻击者蓄意制造误报」确立为一个独立的攻击类别，并给出攻防双方成本函数的博弈结构（p.7、p.9）。量化读数：SpamBayes 上 Aspell 字典攻击诱发的 **10% 误报率即使垃圾邮件过滤器不可用**（p.19）。"
method: "三轴分类学（influence × violation × specificity）＋ 攻防成本敏感博弈的正式结构；以 SpamBayes 统计垃圾邮件过滤器为实例验证 Causative Availability 攻击（字典攻击／聚焦攻击）并讨论 RONI 防御"
baseline: "不适用（分类学与形式化论文）；对照对象为既有攻击文献的逐项归类（p.12–p.18）与 SpamBayes 上的攻击实验（p.19–p.20）"
aliases:
  - Barreno2008-机器学习安全
  - The Security of Machine Learning
  - availability attack taxonomy
related:
  - "[[2026-Barbierato-告警疲劳攻击与告警投毒]]"
  - "[[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]"
---

# Barreno 等：对抗机器学习的威胁模型与「误报＝可用性攻击」分类学

> Marco Barreno、Blaine Nelson、Anthony D. Joseph、J. D. Tygar（UC Berkeley），2008，UCB/EECS-2008-43 技术报告，26 页 · 原件 `raw/papers/attack-detection/2008-Barreno-Security-of-Machine-Learning.pdf`

## 证据等级

**本地全文**。原件已下载（UCB/EECS-2008-43，259,810 字节，SHA-256 `f65321cc2714ada9fc2f429054f0f5966b6ced0c5e29c0eff5b53673d3821dec`，26 页）；经 MinerU `extract` 模式转 Markdown 后用 `pypdf` 逐页文本索引复核页码锚点（2026-09-11）。**本笔记所有页码指 TR 版本页码（PDF 页 ＝ 印刷页，逐页核对 26 页）**。

### ⚠️ 版本关系（引用前必读）

TR 正文 **p.9** 自述：*"A preliminary version of this taxonomy appears in previous work [Barreno et al. ...]"*；参考文献（**p.23**）列出 *"Can machine learning be secure? In Proceedings of the ACM Symposium on InformAtion, Computer, and Communications Security (ASIACCS'06), March 2006."*

因此三版关系是：

| 版本 | 载体 | 关系 | 可得性 |
| --- | --- | --- | --- |
| **2006** · *Can Machine Learning Be Secure?* · ASIACCS'06, pp.16–25 | ACM | **分类学的初步版（优先权在此）** | **付费墙；本轮未取得**（见下） |
| **2008** · *The Security of Machine Learning* · UCB/EECS-2008-43 | UC Berkeley 机构技术报告 | **扩展版；本笔记的事实源** | 公开（本机已入库） |
| **2010** · *The security of machine learning* · Machine Learning 81(2):121–148 | Springer | 期刊版 | 付费墙 |

**入库取舍如实登记**：任务初始要求取 2006 ASIACCS「CMU 公开版」，但**该版本不存在 CMU 公开副本**（检索确认：只有 ACM 版与 Berkeley 的 TRUST 海报）。按 `raw/AGENTS.md`「不使用不可信镜像」的纪律，未采用第三方课程页副本，改用**作者所在机构的公开技术报告**（同一作者群、同一分类学、且自述与 2006 版同源）。**引用时须同时标注两个版本**：优先权归 2006 ASIACCS，页码与形式化细节出自 2008 TR。

## 一句话

把「攻击者让学习器**把良性判成恶意**」正式定义为一个独立攻击类别（Availability attack），并用成本敏感博弈给出它的结构——这是本课题「误报注入」威胁模型的上位理论来源。

## 威胁模型（p.7）

- **定义（p.7 原文）**：*"A threat model is a profile of attackers, describing motivation and capabilities."*（威胁模型是攻击者的画像，描述其**动机**与**能力**。）
- **安全目标（p.7）**：*"Availability goal: To prevent attackers from interfering with normal operation."*（可用性目标：阻止攻击者干扰正常运行。）
- **成本假设（p.7）**：*"We assume that the attacker and defender each have a cost function that assigns a cost to each labeling for any given instance."*（攻防双方各有一个成本函数，为任意实例的每种标注赋予成本。）
- 论文把安全分析拆成「识别安全目标 + 威胁模型」两步（p.7：*"Properly analyzing the security of a system requires identifying security goals and a threat model."*）。

## 三轴分类学（p.5、p.8）

| 轴 | 取值 | 含义 | 锚点 |
| --- | --- | --- | --- |
| **影响面** Influence | **Causative** | 攻击者能影响**训练**过程 | p.5、p.8 |
| | **Exploratory** | 只利用**已有**弱点，不影响训练 | p.5、p.8 |
| **安全目标** Violation | **Integrity** | 瞄准**漏报**（false negatives），让有害输入进入系统 | p.5、p.8 |
| | **Availability** | 瞄准**误报**（false positives），让良性输入无法进入系统 | p.5、p.8 |
| **特异性** Specificity | **Targeted** | 只针对特定输入 | p.5 |
| | **Indiscriminate** | 使一大类输入失败 | p.5 |

三轴独立 ⇒ 至少 **8 个不同攻击类别**（p.5）。

**误报／漏报的判据定义（p.5 原文）**：*"A classification error is a **false positive (FP)** if a normal instance is classified as positive and a **false negative (FN)** if an intrusion instance is classified as negative."*

## 「误报＝可用性攻击」的正式表述（本笔记的核心，供 H 臂威胁建模引用）

| 锚点 | 原文 | 含义 |
| --- | --- | --- |
| **p.5** | *"they may be attacks on Integrity aimed at false negatives … or they may be attacks on **Availability aimed at false positives (preventing benign input from entering a system)**"* | 分类学总述：可用性攻击 ↔ 误报 |
| **p.7** | *"Likewise, **false positives tend to violate the availability goal because the learner itself denies benign instances**."* | **机制陈述：误报由学习器自身执行拒绝**——不是旁路，而是让防御系统自己变成拒绝服务的手柄 |
| **p.7** | *"In general the attacker wants to access system assets (with false negatives) or **deny normal operation (usually with false positives)**."* | 攻击者目标二分 |
| **p.8** | *"**Availability attacks cause denial of service, usually via false positives.**"* | **最正式的一句定义** |
| **p.8** | *"to create a denial of service, usually by **inducing false positives, in which benign instances are incorrectly filtered** (an Availability violation)"* | 与 Integrity 并列的完整表述 |
| **p.9** | *"an Integrity attack benefits the attacker on false negatives … and an **Availability attack focuses high cost on false positives**"* | 成本函数形状：可用性攻击把高成本压在误报上 |

**对本课题最重要的一条结构事实（p.9）**：成本函数的形状取决于攻击类别——**可用性攻击把高成本集中在误报上**。这为「误报预算」提供了形式化位置：它是**成本函数的形状参数**。

## 攻击实例与量化读数

| 类别 | 实例 | 锚点 |
| --- | --- | --- |
| **Causative Availability**（"the rogue IDS"） | 攻击者通过对训练实例的控制干扰系统运行，如阻断合法流量 | **p.10** |
| **Exploratory Availability**（"the mistaken identity"） | 不影响训练，直接干扰 | **p.10** |
| Causative Availability on Polygraph | Newsome 等对多形态病毒检测器 Polygraph 的攻击 | p.13 |
| Causative Availability on Autograph | Chung & Mok 对蠕虫签名生成系统：攻击节点发送模仿目标流量的报文，使 Autograph 学到阻断合法访问的规则 **⇒ 造成拒绝服务** | p.13 |
| Causative Availability on SpamBayes | Nelson 等（Targeted + Indiscriminate 均有） | p.13、p.19 |

**量化读数（p.19）**：*"All of our attacks require relatively few attack emails to significantly degrade SpamBayes's accuracy; **even the 10% false positive rate induced by the Aspell dictionary attack renders a spam filter unusable**."*

- 这是本课题可引的**唯一一个把「误报率」直接连到「系统不可用」的量化锚点**：**10% 误报率 ⇒ 不可用**（SpamBayes / 垃圾邮件过滤场景）。
- 图件锚点：**p.20** 给出三种字典攻击（optimal / Usenet 字典 / Aspell 字典），初始训练集 10,000 封（50% spam）；纵轴是**测试集正常邮件被误分类的百分比**。
- **字典攻击机制（p.19）**：用大词表（如 Aspell 词典、Usenet 语料高频 90,000 词）作为攻击特征，近似最优攻击（*"this optimal attack is intractable, but we approximate its effect by using a large set of common words"*）。

**一条对本课题直接有用的空白陈述（p.14）**：*"However, **Exploratory Availability attacks against the learning components of systems are not common**."*（针对学习组件的探索式可用性攻击**并不常见**。）

## 可迁移机制

1. **「误报」有形式化的攻击位置**（p.7、p.9）：误报不只是评测指标，它是 **Availability 攻击的目标函数形状**。任何以「固定误报预算」为工作点的检测系统，其成本函数天然有一个可被攻击者瞄准的方向。
2. **威胁模型＝动机 × 能力**（p.7）：这是撰写本课题威胁模型一节的**最小充分结构**，可直接采用。
3. **量化阈值存在先例**（p.19）：`10% FP ⇒ 不可用`。本课题若要给「误报预算耗尽」一个量级锚点，**可引用该数值作为不同场景的先例**，但**不得**把它当作本课题数据上的门槛（场景、模型、指标口径都不同）。
4. **攻击者只需很少样本即可造成大幅退化**（p.19）：与 DGA 字符扰动「低成本、大批量」的威胁假设同向。
5. **成本敏感博弈结构**（p.7、p.9）：攻防双方的交互被写成成本函数下的博弈——与本课题「双侧组相对」的攻防结构同源，可作为「为何讨论误报代价」的理论框架引用。

## 不能直接声称内容

- **不能把本笔记的页码用于 2006 ASIACCS 版引用**：本笔记页码全部来自 **2008 TR**（26 页）。2006 会议版 10 页（pp.16–25），页码与措辞都可能不同。**引用 2006 版的具体页码前必须取得该版全文**。
- **不能声称本文提出了「告警预算耗尽」或「告警疲劳」攻击**：本文的可用性攻击目标是**让学习器拒绝良性输入**（SpamBayes 场景），**没有**涉及安全运营中心的**分析师人力预算**、告警队列或告警疲劳。后者的命名见 [[2026-Barbierato-告警疲劳攻击与告警投毒]] 与 [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]。
- **不能把 SpamBayes 的 `10%` 当作本课题的误报门槛**：场景（垃圾邮件过滤 vs 加密流量 DGA 检测）、模型（朴素贝叶斯 vs 神经网络）、指标口径（测试集正常邮件误分类百分比 vs 固定 FPR 工作点下的检测率）均不同。
- **不能声称本文验证了「误报注入作为训练信号」**：本文是**攻击侧**的分类学与攻击实验，**没有**任何防御侧的训练方法。
- **不能忽略版本优先级**：分类学的优先权在 2006 ASIACCS，本文自述其分类学为「preliminary version appears in previous work」（p.9）。

## 与课题的关系

- 本课题 H 臂「双侧组相对对抗训练」的威胁模型若要在正文中站住，**上位理论来源是本文的 Availability attack**：攻击者通过制造误报使检测系统拒绝正常输入。
- **差量定位（文献层）**：本文与后续两篇（[[2026-Barbierato-告警疲劳攻击与告警投毒]]、[[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]）都停在**威胁建模与影响评估**；**没有一篇把该威胁模型反用为防御侧的训练信号**。这是本课题的机制差量所在。
- **可引的量化先例**：`10% FP ⇒ 不可用`（p.19）——只作**量级参照**，不作门槛。
- **可引的空白陈述**：`Exploratory Availability attacks against the learning components of systems are not common`（p.14）——支持「该攻击面在防御侧研究不足」的表述。

## 疑问 / 待验证

- 2006 ASIACCS 版与 2008 TR 版在分类学措辞上的差异**未逐句比对**（缺 2006 全文，见版本说明）。
- 2010 *Machine Learning* 期刊版与 2008 TR 的差异**未核验**（期刊版付费墙）。
- p.20 的图只有曲线，正文未给出「攻击邮件占比 → 误报率」的完整数值表；`10%` 是正文给出的**唯一**具体误报数值。
- 本文的可用性攻击全部在 SpamBayes（朴素贝叶斯系）上验证，**未在神经检测器上验证**。

## 文献信息

- **原件**：`raw/papers/attack-detection/2008-Barreno-Security-of-Machine-Learning.pdf`（UCB/EECS-2008-43，259,810 字节，26 页，SHA-256 `f65321cc2714ada9fc2f429054f0f5966b6ced0c5e29c0eff5b53673d3821dec`）
- **来源**：`https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-43.pdf`（UC Berkeley EECS 技术报告库，2026-09-11 取得）
- **会议初步版**：*"Can machine learning be secure?"*，ASIACCS'06，pp.16–25，DOI `10.1145/1128817.1128824`（**本轮未取得全文**）
- **期刊扩展版**：*"The security of machine learning"*，Machine Learning 81(2):121–148，2010，DOI `10.1007/s10994-010-5188-5`
- **转换**：MinerU `extract` 模式，产物在 `/tmp/fp-inject/md/`（一次性中间物，未入库）
