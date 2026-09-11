---
title: "Paragraph: Thwarting Signature Learning by Training Maliciously（投毒使自动签名生成器被迫在误报与漏报之间取舍）"
authors: [James Newsome, Brad Karp, Dawn Song]
year: 2006
date: 2026-09-11
journal: "RAID 2006（9th International Symposium on Recent Advances in Intrusion Detection）, LNCS 4219, pp.81–105, Springer；DOI 10.1007/11856214_5；20 页"
source_pdf: "[[raw/papers/attack-detection/2006-Newsome-Paragraph-Thwarting-Signature-Learning.pdf]]"
tags:
  - 数据投毒
  - 自动签名生成
  - 误报
  - 可用性攻击
  - 对抗机器学习
  - 类型/论文
key_finding: "提出 **delusive adversary**（攻击者提供的样本**标签全部正确**，只操纵特征）也能让学习器无法生成可用分类器（p.2），并给出两种针对 Polygraph 式自动蠕虫签名生成器的投毒攻击。其中 **Correlated Outlier attack**（§3，p.12–14）的机制是：攻击者选取一批**在正常流量池中以一定频率共现**的伪特征，使「含全部伪特征」的正常样本获得**高于**目标类样本的 Bayes 分数，从而**迫使学习器在「对正常流量误报」与「100% 漏报」之间二选一**（p.13）。这是「**投毒攻击使检测器双侧错误风险被迫取舍**」的最早形式化表述之一。"
method: "威胁模型（delusive adversary）+ 对 Polygraph 的 Bayes 学习器与阈值选择的攻击构造（Dropped Red Herring / Randomized Red Herring / Correlated Outlier / Chaff-based）+ 参数化分析与数值评估"
baseline: "Polygraph 的原始阈值规则「在正常池中不超过 F% 误报」；对照为「取零误报阈值 `T_zfp`」等替代规则"
aliases:
  - Newsome2006-Paragraph
  - Correlated Outlier attack
  - delusive adversary
related:
  - "[[2008-Nelson-垃圾邮件过滤器的可用性攻击]]"
  - "[[2008-Barreno-机器学习安全与误报可用性攻击]]"
---

# Newsome、Karp、Song：投毒迫使签名学习器在误报与漏报之间取舍

> James Newsome、Brad Karp、Dawn Song（CMU / UCL），2006，RAID 2006，LNCS 4219:81–105，DOI `10.1007/11856214_5`，20 页 · 原件 `raw/papers/attack-detection/2006-Newsome-Paragraph-Thwarting-Signature-Learning.pdf`

## 证据等级

**本地全文**。原件已下载（199,991 字节，SHA-256 `54b63af7eb9ab225f4d3d808bd6ad275970eaeb1d08493a1a79cfa01404d38c1`，20 页）；经 MinerU `extract` 转 Markdown 后用 `pypdf` 逐页复核页码锚点（2026-09-11）。**页码即 PDF 页＝印刷页**。

**来源**：作者 Dawn Song 本人的 Berkeley 主页副本（`https://people.eecs.berkeley.edu/~dawnsong/papers/paragraph.pdf`），属**作者自存全文**，符合 `raw/AGENTS.md` 的合法可信来源要求（未使用第三方镜像或付费墙绕过）。

**对 [[2008-Nelson-垃圾邮件过滤器的可用性攻击]] §6 转述的更正**：Nelson 等把本文的 correlated-outlier attack 概括为「向正类训练样本加入伪特征，使学习器阻断带这些特征的正常流量（a Causative Availability attack）」（Nelson p.9）。**本文原文读来更精确**：其核心不是单纯「加入伪特征」，而是**选取在正常池中共现的伪特征组合，使误报曲线右移、从而迫使学习器在误报与 100% 漏报之间二选一**（p.13）。引用时应以**本文原文**为准，Nelson 的转述只作二级线索。

## 一句话

在一个「自动从流量学签名、并按目标误报率选阈值」的系统里，攻击者只要提供**标签全对**的样本，就能把学习器逼进「要么放走全部恶意、要么大量阻断正常流量」的二选一。

## 威胁模型：delusive adversary（p.1–p.2、p.5）

- **定义（p.2 原文）**：*"We show that a **delusive** adversary can manipulate the training data to prevent a learner from generating an accurate classifier, **even if the training data is correctly labeled**."*（脚注 p.2：*delusive: Having the attribute of deluding*。）
- **攻击者可操纵的对象（p.2 原文）**：*"…the **target-class training data**, the **innocuous training data**, or both, **all toward forcing the generation of a classifier that will exhibit many false positives and/or false negatives**."*
- **前提条件（p.5 原文）**：*"…attacks of both types that assume **only a delusive adversary**—one who provides the learner with correctly labeled training data, but who manipulates the **features** in the target-class samples to mislead the learner."*
- **与后续文献的关系**：Nelson 2008 把这类攻击归入 **Causative Availability attack**（其 p.9 转述本文）。**本文是这条链上可核原文的最早一环。**

## 被攻击系统的结构（p.10–p.11）

Polygraph 的阈值选择规则（**这是攻击的着力点**）：

- 训练数据被分成 **innocuous pool**（正常）与 **suspicious pool**（可疑/目标类）（p.10, Fig. 5–6）。
- **阈值 `τ` 取「在 innocuous pool 中误报率不超过 `F%`」的值**（p.11 原文：*"τ is chosen as the value that achieves a false positive rate of no more than F% in the innocuous pool"*）。
- 备选规则 `T_zfp` = 「使 innocuous pool 零误报的最低值」；p.11 指出在其实例中**少数离群点使零误报不可能**，除非把全部真实蠕虫样本也误分类。
- 单调性（p.11）：阈值升高 ⇒ 误报单调下降、漏报单调上升。

## 攻击族与关键结论（§3 起）

| 攻击 | 机制 | 锚点 |
| --- | --- | --- |
| **Dropped Red Herring** | 伪令牌人为把漏报曲线右移；当学习器收到不含该伪令牌的目标类样本时曲线左移，阈值 `τ` 被拖到 `T′_zfn` | p.12, Fig. 7 |
| **Correlated Outlier attack** | **本文最有价值的一种**：攻击者选取在正常池中**以一定频率共现**的伪特征，使「含全部伪特征」的正常样本的 Bayes 分数**高于**目标类样本 ⇒ 学习器被迫在**误报正常流量**与**100% 漏报**之间选择 | **§3, p.12–14** |
|  其参数 | `α`＝伪特征个数；`β`＝每个目标类样本含伪特征的比例；`P(W\|−)`＝目标类特征在正常池中的频率；`P(s_i\|−)`＝伪特征在正常池中的频率 | **p.14**（Theorem 5） |
|  实操策略 | *"identify a type of request in the protocol that occurs in a **small but significant fraction of requests (e.g. 5%)**, and that contains a few features that are not commonly found in other requests"* | **p.13** |
| **Chaff-based 变体** | 在 suspicious pool 中放入「chaff」（含全部伪特征但可被判为阳性的样本），使攻击者可在真实目标类样本中少放甚至不放伪特征 | **p.15**（Theorem 6） |
| **关键对比** | 采用「不超过 `F%` 误报」的阈值规则**对 Dropped Red Herring 稳健**，但**对 Correlated Outlier attack 不稳健** | **p.12–p.13** |

- **核心权衡（p.13 原文）**：攻击者的目标是选择一个伪特征集合，使得学习器 *"either to have innocuous samples containing the spurious features as **false positives**, or to have **100% false negatives**"*。
- **成功条件（p.13）**：伪特征要**在正常池中出现得足够少**（使 `P(S|+)/P(S|−)` 足够大），又要**出现得足够频繁**（使正常池中有相当比例的样本含全部伪特征）。
- **图 9／图 10（p.14）**给出攻击有效性的数值评估（横轴 `Max P(s_i|−)`，含不同 `α`／`β`／chaff 比例 `N`）。

## 对本课题的直接相关性（**本课题推论，非原文主张**）

**这是本课题「双侧错误风险」结构在投毒文献中的早期形式化先例，必须正视**：

| 本课题的结构 | 本文的对应结构 | 差异 |
| --- | --- | --- |
| 攻击者制造 DGA 扰动变体 ⇒ **漏检压力**（FN） | Dropped Red Herring：伪令牌抬高漏报 | 本文是**特征投毒**，本课题是**输入扰动** |
| 攻击者制造良性近邻 ⇒ **误报压力**（FP） | **Correlated Outlier attack：直接制造误报压力** | 本文是**训练数据的特征选择**，本课题拟用**训练信号的组织方式** |
| 双侧同时施压 ⇒ 迫使防御方在两侧取舍 | p.13 的「二选一」正是该结构 | 本文是**攻击侧**分析，**无防御侧训练方法** |

**因此**：
1. 「双侧错误风险」这一**威胁结构**在 2006 年已有先例（本文），**不得写成本课题首创**；
2. 但本文停在**攻击可行性分析**，**没有**任何把该结构反用为**训练信号**（让模型同时抵抗两侧压力）的做法——**这是本课题仍然可能成立的差量所在，须由实验裁决**；
3. **引用纪律**：正文明言本文时须同时说明「本文是攻击侧分析、无防御侧训练方法」，不得让读者误以为本课题的「双侧」是全新概念。

## 可迁移机制

1. **「标签全对」不足以防护投毒**（p.2）：delusive adversary 的样本标签正确，危害来自**特征选择**。对本课题的含义是：**只校验标签正确性不足以排除污染**（本课题推论）。
2. **阈值规则本身是攻击面**（p.11–p.13）：Polygraph 的「不超过 F% 误报」规则对一种攻击稳健、对另一种不稳健。**给定一个误报约束并不自动带来安全性**——这是本课题「干净 FPR 护栏」必须搭配检出侧判据的**外部理由**（本课题推论）。
3. **攻击者只需少量协议常识**（p.13）：选「出现率约 5%、特征不常见」的请求类型即可，无需看到正常池。**低门槛**是该攻击的威胁性来源。
4. **攻击的参数化刻画**（p.14, Theorem 5）：`α`／`β`／`P(W|−)`／`P(s_i|−)` 四个参数决定成败——是「把攻击写成可分析对象」的范例。

## 不能直接声称内容

- **不能声称本文提出了防御方法**：本文是**攻击侧**分析（标题里的 "Thwarting" 指被攻击系统的设计目标，不是本文提出的防御）。
- **不能把本文与 [[2008-Nelson-垃圾邮件过滤器的可用性攻击]] 的转述当作两条独立证据**：Nelson §6 对本文的概括是**二级转述**，且本文原文的机制更精确（见上文更正）。
- **不能把本文的 `F%`、`5%`、`α`／`β` 取值搬作本课题的门槛**：场景（蠕虫签名生成 vs DGA 检测）、数据（协议请求字节特征 vs 域名字符串）、指标口径均不同。
- **不能声称本文涉及 SOC、告警队列或分析师人力**：与 [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]、[[2026-Barbierato-告警疲劳攻击与告警投毒]] 不是同一后果链。
- **不能把「双侧错误风险」写成本课题首创**：本文（2006）已有该结构的攻击侧形式化。
- **本文的网络场景是蠕虫签名生成，不是机器学习分类器训练**：Polygraph 的 Bayes 学习器是签名生成器的一部分，与神经检测器的训练过程差异很大。

## 疑问 / 待验证

- 本文的**攻击实验是在 Polygraph 实现上做的还是纯分析**：p.14 有数值评估图（Fig. 9、Fig. 10），但**是否为真实系统实现未逐节确认**；引用「实验有效」前须回 §4 起核对。
- 本文的代码与数据**未核**。
- **Allergy 攻击原文（Chung & Mok, RAID 2006, LNCS 4219:61–80, DOI `10.1007/11856214_4`）本轮仍未取得**（Springer 付费墙；仅见第三方聚合站副本，按纪律未采用）——它与本文同属 RAID 2006 的自动签名生成投毒线，**引用 Allergy 时只能标「据 Nelson 2008 §6 转述」**。
- 本文与 Nelson 2008 的**内容重叠度未逐句比对**。

## 文献信息

- **原件**：`raw/papers/attack-detection/2006-Newsome-Paragraph-Thwarting-Signature-Learning.pdf`（199,991 字节，20 页，SHA-256 `54b63af7eb9ab225f4d3d808bd6ad275970eaeb1d08493a1a79cfa01404d38c1`）
- **来源**：作者 Dawn Song 主页（UC Berkeley EECS，2026-09-11 取得）
- **题录**：RAID 2006, LNCS 4219, pp.81–105, Springer；DOI `10.1007/11856214_5`
- **转换**：MinerU `extract` 模式，产物在 `/tmp/near/md/`（一次性中间物，未入库）
