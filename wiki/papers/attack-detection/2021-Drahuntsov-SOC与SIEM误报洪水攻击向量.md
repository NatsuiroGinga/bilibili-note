---
title: "Potential Disguising Attack Vectors on Security Operation Centers and SIEM Systems（以误报噪声掩盖真实攻击的伪装攻击向量）"
authors: [Roman Drahuntsov, Dmytro Rabchun]
year: 2021
date: 2026-09-11
journal: "Кібербезпека: освіта, наука, техніка（Cybersecurity: Education, Science, Technique）, vol. 2(14), 2021, pp. 6–14；DOI 10.28925/2663-4023.2021.14.614"
source_pdf: "[[raw/papers/attack-detection/2021-Drahuntsov-Disguising-Attack-Vectors-SOC-SIEM.pdf]]"
tags:
  - 安全运营中心
  - SIEM
  - 误报
  - 告警疲劳
  - 规避攻击
  - 类型/论文
key_finding: "把「**用误报噪声掩盖真实恶意活动**」正式命名为 **disguise attacks**（伪装攻击），并给出三个具体攻击向量：① **伪造日志生成**——向 SIEM 灌入海量看似合理的假日志，撑爆许可 EPS 配额，使真实事件无法被完整接收（印刷 p.8–9）；② **关联规则逻辑缺陷利用**——逆向关联规则的前置条件，人为凑出「**没有真实事件却触发了告警**」的假事件，大量假事件**消耗 SOC 分析师时间**，从而让真实攻击「更有可能不被发现或低估」（印刷 p.10–11）；③ **「狼来了」式消耗**——反复触发某条规则，诱使安全团队**关闭这条「烦人」的检测规则**（印刷 p.11–12）。核心原句（摘要，印刷 p.6）：*\"An attacker may trigger the malfunctioning alarm continuously to distract the analytics stuff and perform its actions under the cover of noise.\"*"
method: "概念性与设计分析论文（作者自述为 conception，源自对多个生产环境 SIEM 部署的实践考察）；无实验、无数据集、无量化读数"
baseline: "不适用；对照组为既有 SOC/SIEM 最佳实践与 SANS／NSA／Ponemon 等报告"
aliases:
  - Drahuntsov2021-伪装攻击
  - disguise attacks
  - false positive alarm flooding
related:
  - "[[2008-Barreno-机器学习安全与误报可用性攻击]]"
  - "[[2026-Barbierato-告警疲劳攻击与告警投毒]]"
---

# Drahuntsov & Rabchun：用误报噪声掩护真实攻击的三个「伪装攻击」向量

> Roman Drahuntsov、Dmytro Rabchun（State University of Telecommunications, Kyiv），2021，*Cybersecurity: Education, Science, Technique* 2(14):6–14，DOI `10.28925/2663-4023.2021.14.614` · 原件 `raw/papers/attack-detection/2021-Drahuntsov-Disguising-Attack-Vectors-SOC-SIEM.pdf`

## 证据等级

**本地全文**。原件已下载（568,455 字节，SHA-256 `79d510a9a9990a8b3af9d95cf478fc358e3979975d2f6fb07171457d88b27fcb`，9 页）；经 MinerU `extract` 转 Markdown 后用 `pypdf` 逐页复核页码锚点（2026-09-11）。

**页码换算**：PDF 页 `N` ＝ **印刷页 `N+5`**（逐页页眉核对：PDF p.1 页眉为 `6`，…，PDF p.7 为 `12`，PDF p.9 为 `14`）。**本笔记页码一律用印刷页。** 文章正文为英文（印刷 pp.6–12），印刷 pp.13–14 为**乌克兰语同文**与参考文献。

### ⚠️ 两项必须随结论转述的自限（原文自述）

1. **本文是概念性论文**：无实验、无数据集、无量化读数、无形式化威胁模型；作者自述 *"we are about to set up a conception that is a result of practical exploration of several SIEM systems used in production environments"*（印刷 p.7），三个向量"derived from analysis of the actual SIEM installations and SOC processes used as best practices"（印刷 p.6）。
2. **作者明确声明无在野证据**：*"We have **no actual indicators that those attacks are carried out 'in wild'** at the moment of issuing of this article, but it is highly probable that those tactics may be used in the future."*（摘要，印刷 p.6）；结论节重申 *"Despite we have **no data about usage of those tactics in actual security incidents** we are aware of that in future."*（印刷 p.12）。

> **引用纪律**：因此本文只能支撑「该攻击模式已被**正式命名并具体化为攻击向量**」，**不能**支撑「该攻击已在真实环境出现」，也**不能**作为任何发生率或效果量级的依据。

## 核心定义：disguise attack（伪装攻击）

**引言（印刷 p.6 原文）**：*"we call it **"disguise" attacks** because of actual purpose to carry out one – **to hide the malicious activity under the hood of "noise" of false positive alarms** or other monitoring malfunctions."*

**摘要（印刷 p.6 原文，最常被引的一句）**：*"An attacker may trigger the malfunctioning alarm continuously to **distract the analytics stuff and perform its actions under the cover of noise**."*

**关键词（印刷 p.6）**：Security Operation Center; SIEM; Evasion; Disguise; Monitoring; Defense evasion; Adversary tactics.

## 三个攻击向量（印刷页锚点）

### 向量 1：伪造日志生成（FAKE LOG GENERATION，印刷 pp.8–9）

- 机制（p.8）：生成**海量**看似合理、格式与真实事件源一致、SIEM 可解析的假日志，投递到 SIEM 日志采集端点，经聚合处理后产生**异常体量的新事件**，可能导致关联（correlation）停顿、算力过载、**无关告警激增**。
- 前提（p.8–9）：攻击者需控制某个 SIEM 已连接端点（如运行 rsyslog 的服务器），或在 SIEM 接收范围配置不当的情况下从外部设备发起。
- **量化后果（p.9，操作性而非实验读数）**：
  1. *"SIEM is overflowed with fake events, **licensed EPS volume is exceeded**, new actual events will not be accepted in full scale – the simultaneous security incidents may be missed by the software and overlooked by the security team"* —— **许可 EPS 配额被撑爆 ⇒ 真实事件无法完整接收**。这是本课题「告警预算耗尽」最直接的机制表述。
  2. 硬件因关联负载上升而过载，系统脱离正常工作流。
  3. **安全团队把过多时间花在异常日志源上，而真正的攻击工作流可能比这场干扰"安静得多"**（p.9）。

### 向量 2：关联规则逻辑缺陷利用（印刷 pp.10–11）——**与「误报注入掩护」最贴合**

- 机制（p.10）：SIEM 告警是关联规则这一逻辑函数的正结果。攻击者可**逆向该逻辑函数**，把输入参数（事件、流等）排布成满足前置条件的样子。
- **攻击本质（p.10 原文）**：*"The attack's essence is in the fact that **there were no actual incident but the alert still raised**."*（没有真实事件，但告警仍被触发。）
- **效果（p.10 原文）**：*"**Significant amount of such "fake" incidents may consume too much SOC specialists' time and reduce the overall efficiency. Therefore, an adversary has more chances to stay undetected or underestimated in its real malicious activity.**"* —— **这是本课题「误报注入以掩护真实攻击」的逐字文献表述。**
- 成因（p.10）：关联规则中的判据数组**冗余**，因此不唯一对应真实事件；作者用「真实事件集合 vs SIEM 判为事件的集合」两集合的关系刻画，落在前者之外的即误报（p.10）。
- 升级形态（p.11）：攻击者从**与真实攻击无关的旁路基础设施**发起一连串利用尝试与 C2 建链，"in noisy fashion"；SIEM 无法区分真实成功攻击与恶意活动的成串模仿；集中短时爆发的异构告警会**让安全人员误以为发生了大规模复杂事件**，而真正被精心伪装的实际攻击可在转移注意期间**留在雷达之下**。

### 向量 3：「狼来了」（THE SHEPHERD'S BOY AND THE WOLF，印刷 pp.11–12）

- 机制（p.11–12）：选择一条**配置良好、确实能捕到真实威胁、但也容易产生误报**的关联规则。攻击者反复满足其触发条件 ⇒ 安全团队调查后按误报关闭 ⇒ 攻击者再次触发 ⇒ *"it is highly probable, that **"annoying" detector will be disabled till redesign**, or further investigations will not be performed deeply"*。
- 作者的归因前提（p.11–12）：*"as **most of the SIEM alerts are false positives**"* —— 该攻击之所以可行，正建立在防御方日常已被误报淹没之上。

## 可迁移机制

1. **「误报」是攻击者可主动生产的资源，而非被动的系统缺陷**（印刷 p.10）：向量 2 把误报从"检测器性能问题"改写成"攻击者的可控输入"。这是本课题把误报注入当作威胁模型的**定义级来源**。
2. **误报消耗的是有限资源**（印刷 p.10「consume too much SOC specialists' time」；p.9「licensed EPS volume is exceeded」）：本文给出两种可耗尽的预算——**分析师时间**与**许可事件吞吐**。二者都是**预算**，可对应到检测系统的工作点约束。
3. **「关闭规则」是该攻击的终态**（印刷 p.11–12）：向量 3 说明误报的累积效应不只是延迟，而是**使检测能力被防御方自己移除**。这是"告警预算耗尽"最强的形式化后果。
4. **两集合刻画**（印刷 p.10）：「真实事件集合」与「SIEM 判为事件的集合」的重叠关系——提供了把误报与漏报放在同一框架下讨论的直观工具。

## 不能直接声称内容

- **不能声称该攻击已在野外出现**：作者两次明确否定（印刷 p.6、p.12）。
- **不能声称本文提供了实验数据、检测率、误报率或任何量化读数**：全文无实验、无数据。
- **不能把本文的「EPS 配额」「分析师时间」直接等同于本课题的固定 FPR 工作点**：本文的对象是 SIEM 许可与分析流程，不是机器学习检测器的 ROC 工作点；二者的"预算"只是同构的**隐喻**，需在正文中说明这一层转换是**本课题的建模选择**而非原文主张。
- **不能声称本文提出了训练方法或防御机制**：本文只到提升风险与原则性缓解方向（印刷 p.12：*"we are looking forward to have experimental proof-of-concept for or against described conception"*）。
- **注意本文的证据形态**：它是**概念性（conception）**论文，被引时须与实验型论文区分证据等级。

## 与课题的关系

- 本课题 H 臂的威胁模型表述若要**有正式文献支撑**，本文是**最直接的一篇**：它把「攻击者制造误报 ⇒ 消耗防御方资源 ⇒ 真实攻击被掩护」写成完整因果链，并给出三个具体向量。
- **与 [[2008-Barreno-机器学习安全与误报可用性攻击]] 的分工**：Barreno 提供**上位分类学**（Availability attack，误报作为安全目标被瞄准）；本文提供**面向安全运营的具体攻击向量与命名**（disguise attack）。两者层级不同，**引用时不得混为一谈**（Barreno 未涉及分析师人力与告警队列）。
- **差量定位**：本文与 Barreno、[[2026-Barbierato-告警疲劳攻击与告警投毒]] 一样，**都停在威胁建模与影响评估**；**没有一篇把该威胁模型反用为防御侧的训练信号**——这正是本课题的机制差量所在。
- **对本课题的一处直接提示**：向量 3（「狼来了」）说明**误报的累积会使防御方主动关闭检测**。这为「干净 FPR 护栏（G3：`ΔFPR ≤ 0`）」提供了**威胁模型层面的理由**——不只是"性能好看"，而是**降低被「狼来了」式攻击诱导关闭的概率**。该理由是**本课题的推论**，本文未如此主张。

## 疑问 / 待验证

- 本文**无形式化威胁模型**（无动机/能力的形式刻画），与 [[2008-Barreno-机器学习安全与误报可用性攻击]] p.7 的 threat-model 定义**不可互换引用**。
- 印刷 pp.13–14 的乌克兰语版本与英文版是否完全同文**未逐句比对**（标题一致、作者一致）。
- 参考文献 [4] Sacher 2020 *Fingerpointing false positives*（*Digital Threats: Research and Practice* 1(1):1–7，DOI `10.1145/3370084`）与 [2] CriticalStart 2019 *The impact of security alert overload* 被本文用作"误报普遍性"的依据，**两者均未入库核验**；若正文要引"误报普遍"的数量级，须先取得这两份来源。
- 出版方 OJS 元数据标注页码为 `6-16`，而**实际页眉为 pp.6–14**（印刷 p.14 为末页）。引用页码以**页眉为准**。

## 文献信息

- **原件**：`raw/papers/attack-detection/2021-Drahuntsov-Disguising-Attack-Vectors-SOC-SIEM.pdf`（568,455 字节，9 页，SHA-256 `79d510a9a9990a8b3af9d95cf478fc358e3979975d2f6fb07171457d88b27fcb`）
- **来源**：期刊文章页 `https://csecurity.kubg.edu.ua/index.php/journal/article/view/309`（Borys Grinchenko Kyiv University 开放获取，2026-09-11 取得）；DOI `10.28925/2663-4023.2021.14.614`；ISSN `2663-4023`
- **转换**：MinerU `extract` 模式，产物在 `/tmp/fp-inject/md/`（一次性中间物，未入库）
