---
title: "Exploiting Machine Learning to Subvert Your Spam Filter（Causative Availability attack：以污染训练数据抬高误报使过滤器不可用）"
authors: [Blaine Nelson, Marco Barreno, Fuching Jack Chi, Anthony D. Joseph, Benjamin I. P. Rubinstein, Udam Saini, Charles Sutton, J. Doug Tygar, Kai Xia]
year: 2008
date: 2026-09-11
journal: "LEET '08（First USENIX Workshop on Large-Scale Exploits and Emergent Threats），2008-04-15，San Francisco，USENIX Association，10 页"
source_pdf: "[[raw/papers/attack-detection/2008-Nelson-Exploiting-Machine-Learning-Subvert-Spam-Filter.pdf]]"
tags:
  - 可用性攻击
  - 数据投毒
  - 误报
  - 对抗机器学习
  - 垃圾邮件过滤
  - 类型/论文
key_finding: "把「**攻击者污染训练数据以抬高误报、使过滤器不可用**」正式命名为 **Causative Availability attack**，并在真实统计过滤器 SpamBayes 上做实验：**攻击者只控制 1% 的训练邮件（10,000 条中的 101 条）即可让过滤器不可用**（p.6）。最尖锐的一个读数是 **Usenet 字典攻击在仅控制 1% 训练邮件时使 36% 的正常邮件被误分类，从而使 SpamBayes 不可用**（p.9）。§3.1 的三分法与 [[2008-Barreno-机器学习安全与误报可用性攻击]] 一致：制造 false negatives 是 Integrity violation，**制造 false positives 是 Availability violation**，本文研究的是前者之外的**后者**（p.4）。"
method: "威胁模型 + 攻击构造（字典攻击／聚焦攻击／最优攻击）+ 在 SpamBayes 上的十折交叉验证实验；并提出两种防御（RONI 与动态阈值）"
baseline: "无防御的 SpamBayes 基线；三种字典攻击变体（Optimal / Usenet 字典 90,000 词 / Aspell 字典）互相对照；初始训练集 10,000 条邮件（50% spam）"
aliases:
  - Nelson2008-Availability attack
  - Causative Availability attack
  - dictionary attack on spam filter
related:
  - "[[2008-Barreno-机器学习安全与误报可用性攻击]]"
  - "[[2006-Newsome-Paragraph-签名学习投毒]]"
  - "[[2026-Barbierato-告警疲劳攻击与告警投毒]]"
---

# Nelson 等：以污染训练数据抬高误报，使检测器不可用（Causative Availability attack）

> Blaine Nelson 等 9 人（UC Berkeley 等），2008，LEET '08（USENIX），10 页 · 原件 `raw/papers/attack-detection/2008-Nelson-Exploiting-Machine-Learning-Subvert-Spam-Filter.pdf`

## 证据等级

**本地全文**。原件已下载（360,912 字节，SHA-256 `1d0402ad708fd745f2fbb31099a086be07f9b051df3af8789d30a885b3ec2096`，10 页）；经 MinerU `extract` 转 Markdown 后用 `pypdf` 逐页复核页码锚点（2026-09-11）。**页码即 PDF 页＝印刷页**（逐页核对）。

**来源**：Edinburgh Research Explorer（爱丁堡大学官方研究仓库，`https://www.pure.ed.ac.uk/ws/portalfiles/portal/11154063/nelson.pdf`；共同作者 Charles Sutton 任职于该校），属**作者所属机构的正式仓库**。USENIX 官方页为 `https://www.usenix.org/conference/leet-08/exploiting-machine-learning-subvert-your-spam-filter`。

**节—页映射（已核）**：§1 p.2｜§2 p.3｜§3（§3.1–§3.3）p.4｜§3.4、§4（§4.1）p.5｜§4.2–§4.3 p.6｜§5（§5.1 RONI）p.7｜§5.2 p.8｜§6 Related work、§7 Conclusion p.9。

## 一句话

在自动学习的检测器上，「让正常对象被判为恶意」不是副作用，而是一个**完整的攻击目标**——2008 年就已有正式命名、明确机制与实验强度。

## 威胁模型与定义（p.4，§3.1）

- **三分（p.4 原文）**：攻击者可以使 *"(a) spam messages slip through the filter (an **Integrity violation**); or (b) to create false positives, in which ham messages are incorrectly filtered (an **Availability violation**)."*
- **本文的研究对象（p.4 原文）**：*"Our focus is on **Causative Availability attacks**, which manipulate the filter's training data to increase false positives."*
- **后果（p.2 摘要）**：*"a broad dictionary attack can render the spam filter unusable, **causing the victim to disable the filter**"*。
- **与 [[2008-Barreno-机器学习安全与误报可用性攻击]] 的关系（必须写清）**：两者是**同一研究组的同一条线**。Barreno 的 TR（UCB/EECS-2008-43）给出**上位分类学**（三轴 + 成本函数 + 博弈结构），**其 p.19 的 SpamBayes 攻击实验明确转引本文**（原文：*"described in full in our earlier paper [Nelson et al. …]"*）；本文是该攻击的**一手全文与实验来源**。**引用时：分类学引 Barreno，实验与逐字威胁模型表述引本文。**

## 攻击构造（§3，p.4–5）

| 攻击 | 机制 | 锚点 |
| --- | --- | --- |
| **字典攻击**（dictionary attack） | 把大量**正常邮件中会出现的词**置入被标为 spam 的攻击邮件，使这些正常词的 spam score 升高，于是**未来的正常邮件更容易被判为 spam** | §3.2, p.4；§3.4, p.5 |
| **聚焦攻击**（focused attack） | 针对**某一类特定正常邮件**使其被过滤；比字典攻击更精准，无需影响其它邮件 | §3.3, p.4；§3.4, p.5 |
| **最优攻击**（optimal attack） | 作为理论上界构造 | §3.4, p.5 |

**字典攻击的材料（p.6）**：Optimal（黑三角）／Usenet 字典（**Usenet 语料前 90,000 高频词**）／Aspell 字典（与 Usenet 字典重叠约 61,000 词）。Usenet 字典效果显著更强，因为它包含拼写错误与俚语等不在标准英语词典中的常见词。

## 量化读数（本笔记登记的核心，供 H 臂威胁建模一节的量级参照）

| 读数 | 原文 | 锚点 |
| --- | --- | --- |
| **1% 控制即可破坏** | *"By **101 attack emails (1% of 10,000)**, the accuracy falls significantly for each attack variation; at this point **most users will gain no advantage from continued use of the filter**."* | **p.6**（§4.2） |
| **1% 即不可用** | *"Each attack renders the filter unusable with as little as **1% control (101 messages)**."* | **p.6** |
| **36% 正常邮件被误分类** | *"Our Usenet dictionary attack causes misclassification of **36% of ham messages with only 1% control** over the training messages, rendering SpamBayes unusable."* | **p.9**（§7） |
| 实验规模 | 初始训练集 **10,000 条邮件（50% spam）**；三种字典攻击变体**十折交叉验证**取平均；Figure 1 纵轴为 **percent of test ham misclassified** | **p.6**（§4.2、图 1） |
| 聚焦攻击强度 | *"a well-informed focused attack can **remove the target email from the victim's inbox 90% of the time**"* | **p.2**（摘要） |

**注意区分两个数字**：`36%`（Usenet 字典攻击下的正常邮件误分类率）与 `10%`（[[2008-Barreno-机器学习安全与误报可用性攻击]] TR p.19 提到的 Aspell 字典攻击下的误报率）**不是同一个攻击变体**，不得混用。

## 同文对两条更早先例的追溯（§6，p.9）——**二级转述，原文未核**

- *"Chung and Mok [2, 3] present a **Causative Availability attack** against the **Autograph** worm signature generation system [10], which infers blocking rules based on patterns observed in traffic from suspicious nodes."*
- *"…adding spurious features to positive training instances, causing the filter to **block benign traffic with those features** (a Causative Availability attack)."*（指 Newsome 等的 Paragraph / correlated-outlier attack）

> ⚠️ 这两条在本笔记中**只能是二级转述**：Allergy 原文（Chung & Mok, RAID 2006, LNCS 4219:61–80, DOI `10.1007/11856214_4`）**本轮未取得全文**（Springer 付费墙；仅见第三方聚合站副本，按 `raw/AGENTS.md` 不使用不可信镜像，未采用）。**引用 Allergy 时必须标「据 Nelson 2008 §6 转述，原文未见」。** Paragraph 原文**本轮已取得并入库**（见 [[2006-Newsome-Paragraph-签名学习投毒]]）。

## 两种防御（§5，p.7–8）——**本文自带的反向证据**

- **RONI（Reject on Negative Impact）**（§5.1, p.7）：逐条检验新增训练样本是否对分类器产生负面贡献，剔除之。初步实验报告 *"identifying **100% of the attack emails without flagging any non-attack emails**"*（p.7）——对字典攻击极有效。
- **动态阈值防御**（§5.2, p.8）：基于分布的自适应阈值；但 p.8 指出其副作用：*"the dynamic threshold causes almost all spam messages to be classified as unsure even when the attack is only 1% of the inbox"*。

**对本课题的含义（推论，非原文主张）**：本文说明「误报注入」是**可检测、可缓解**的（RONI），缓解手段依赖**逐样本的贡献检验**；这与「把误报信号反用为训练信号」是两条不同的技术路线。

## 可迁移机制

1. **「误报」是攻击者的目标函数，不是评测副作用**（p.4）：本文把 availability violation 形式化为「使 ham 被误判」。这是本课题威胁模型的**一手来源**。
2. **攻击成本极低**（p.6）：`1%` 的训练数据控制即足以使系统不可用。**注意：这是垃圾邮件过滤器场景的数值，不得搬作本课题门槛。**
3. **攻击链是「污染训练数据 → 抬高正常词分数 → 未来正常邮件被误判」**（§3.2, p.4）：一个**跨时间的因果链**，而非单步扰动。与 DGA 场景的「同一干净域名生成扰动近邻」是**不同形态**的注入。
4. **缓解手段的副作用可被量化**（p.8）：动态阈值使大量 spam 变成 "unsure"——提示**任何降低误报的机制都会在另一个维度付代价**，与本课题「干净 FPR 与对抗检出双主轴」的理由同向。
5. **同组的分类学论文（Barreno）与其一手实验论文的分工**，是「理论锚点与实证锚点分开引用」的范例。

## 不能直接声称内容

- **不能把本文的 `1%` / `36%` / `10%` 当作本课题的门槛或预期量级**：场景（垃圾邮件 vs DGA 域名检测）、模型（SpamBayes 朴素贝叶斯系 vs 神经网络）、指标口径（测试集正常邮件误分类百分比 vs 固定 FPR 工作点下的检出率）均不同。
- **不能声称本文涉及 SOC、告警队列、分析师人力或告警预算**：本文的对象是**邮件过滤器自身拒绝正常邮件**，**没有**任何安全运营或告警流程内容。把它当成「alert budget exhaustion」的先例是越界引用。
- **不能声称本文提出了防御侧训练方法**：RONI 是**数据筛除**（reject），不是训练信号设计。
- **不能把 §6 对 Allergy / Paragraph 的转述当作对这两篇原文的核验**：Allergy 原文本轮未取得（见上）。
- **不能忽略本文与 Barreno 2008 TR 的同源关系**：两者出自同一研究组、同一条线，**并列引用时须说明「分类学 vs 一手实验」的分工**，否则会被读成两条独立证据。

## 与课题的关系

- **H 臂威胁模型的最强正式锚点**：本文提供了「攻击者故意使正常对象被判恶意以提高 FPR」的**逐字定义 + 明确机制 + 实验强度**。正文写威胁模型时，**分类学引 Barreno 2008、实验与定义引本文**。
- **与 [[2026-Barbierato-告警疲劳攻击与告警投毒]]、[[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]] 的层级区分（必须保持）**：
  - **本文**：误报注入的**机器学习侧一手来源**（污染训练数据 → 抬高 FPR → 系统不可用）；
  - **Drahuntsov 2021**：面向 **SOC/SIEM** 的攻击向量（含"用噪声掩护真实攻击"）；
  - **Barbierato 2026**：**社会—技术动力学**（信任/疲劳/告警压力）。
  三者的**攻击后果链不同**，**不得合并成一条引证**。
- **差量定位（不变）**：三者与 Barreno 都停在**威胁建模、攻击构造或影响仿真**；**未检得**把该威胁模型反用为防御侧训练信号的先例。

## 疑问 / 待验证

- 本文的四个攻击/防御实验均在 **SpamBayes**（朴素贝叶斯系）上做，**未在神经网络检测器上验证**。
- **Allergy 原文（RAID 2006）本轮未获取**，其在 H 臂威胁模型中的位置只能标为「二级转述」。
- 本文的**代码与数据未核**（未见公开仓库；未验证可复现性）。
- 本文的 `Figure 1` 只有曲线，正文未给完整数值表；`36%` 是 §7 结论里给出的**唯一**具体误报数值。
- 本文与 Barreno TR 的**章节内容重叠度未逐句比对**（两者都描述字典攻击）。

## 文献信息

- **原件**：`raw/papers/attack-detection/2008-Nelson-Exploiting-Machine-Learning-Subvert-Spam-Filter.pdf`（360,912 字节，10 页，SHA-256 `1d0402ad708fd745f2fbb31099a086be07f9b051df3af8789d30a885b3ec2096`）
- **来源**：Edinburgh Research Explorer（爱丁堡大学官方研究仓库，2026-09-11 取得）；USENIX 官方页 `https://www.usenix.org/conference/leet-08/exploiting-machine-learning-subvert-your-spam-filter`
- **DOI**：无（USENIX 会议论文；ACM DL 收录号 `10.5555/1387709.1387716`）
- **转换**：MinerU `extract` 模式，产物在 `/tmp/near/md/`（一次性中间物，未入库）
