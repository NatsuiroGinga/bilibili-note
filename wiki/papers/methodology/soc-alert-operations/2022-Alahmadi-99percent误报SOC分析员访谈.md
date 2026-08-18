---
title: "99% False Positives: A Qualitative Study of SOC Analysts' Perspectives on Security Alarms"
authors: [Bushra A. Alahmadi, Louise Axon, Ivan Martinovic]
year: 2022
date: 2026-08-18
journal: "31st USENIX Security Symposium (USENIX Security 22)，2022 年 8 月 10–12 日，美国波士顿，pp. 2783–2800，ISBN 978-1-939133-31-1"
source_pdf: "[[raw/papers/methodology/soc-alert-operations/2022-Alahmadi-99-Percent-False-Positives-SOC-Analysts-USENIXSec.pdf]]"
sha256: "bf9a559479c56202fa7ff409a5b8e58656d4831cde6ddb28b76b832417083ff7"
tags:
  - 告警疲劳
  - 安全运营中心
  - 误报
  - 定性访谈
  - 可处置性
  - 类型/论文
key_finding: "对 20 名问卷 + 21 名访谈的 SOC 从业者的定性研究表明，分析员感知到的误报率极高（受访者 B3 原话把它量化为 99%），但这些「误报」大多是「良性触发」——签名确实匹配、组织出于业务理由选择忽略；验证告警靠的是资产与网络上下文，而不是单条告警本身。"
method: "在线问卷（n=20，SOC 从业者）+ 半结构化访谈（n=21）+ 主题编码分析"
baseline: "无算法基线（定性研究）"
aliases:
  - Alahmadi2022-99PercentFalsePositives
  - 99% False Positives SOC Analysts
related:
  - "[[../2013-Yen-Beehive企业日志大规模行为检测]]"
  - "[[../2012-Bilge-DISCLOSURE大规模NetFlow僵尸网络控制服务器检测]]"
  - "[[2021-Ho-Hopper横向移动路径检测与告警预算]]"
---

# 99% 误报：SOC 分析员如何看待安全告警

> Alahmadi, Axon, Martinovic, 2022, USENIX Security '22 · 18 页

## 一句话

SOC 分析员的瓶颈不是模型准确率，而是「每条告警都必须由人去验证」，而验证靠的是把告警落到具体资产及其业务上下文；缺少上下文的告警即使技术上正确也不可处置。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：99% False Positives: A Qualitative Study of SOC Analysts' Perspectives on Security Alarms
- 作者单位：University of Oxford（三位作者同单位，PDF 第 1 页）
- 会议：31st USENIX Security Symposium，2022 年 8 月 10–12 日，美国马萨诸塞州波士顿（PDF 第 1 页 USENIX 封面页）
- ISBN（封面页）：978-1-939133-31-1
- 页码：pp. 2783–2800（USENIX 会议录页码，取自出版社条目；PDF 正文页脚给出同一编号段）
- 原件：`raw/papers/methodology/soc-alert-operations/2022-Alahmadi-99-Percent-False-Positives-SOC-Analysts-USENIXSec.pdf`

## 论文原结论（全文核验）

1. **告警量本身就是首要限制**（§6 RQ2）。受访者 B3 直言：
   "We know 99% of the alarms we generate are false positives, but we still have to look at them."
   多名受访者与问卷条目 A-1、A-4 都表达了对告警数量的不满。
2. **「误报」这个词被误用**（§6 小结）。多数被分析员称为误报的告警其实是
   「良性触发（benign trigger）」——签名条件确实匹配，但触发原因有业务正当性，组织选择忽略。
   受访者 C5：事件量非常高，「并不意味着它们是误报，而是意味着其中很多是被良性触发引发的」。
   论文因此主张：在真实部署中评估系统性能时，笼统使用 False Positive 会给人「技术本身有根本缺陷」的错误印象。
3. **签名写得太宽会直接导致不可复核**（§7.1）。受访者 A1：
   "if it's just constantly firing, nobody's got the time to review all of them"。
   受访者 G19 用「noisy」形容那些「按设计正常工作但产生不可处置告警」的工具。
4. **验证依赖资产与网络上下文**（§7.3 Alarm Contextuality）。分析员指出 IDS 告警缺少上下文；
   而消除误报、决定调查路径所需的知识正是**关于资产与网络的知识**——网络拓扑与设备、
   设备用途、位置与责任人。论文举例：知道某资产是 Windows 机器，就能快速否定一条 Linux 签名告警。
   分析员还需要业务侧知识（如客户工作时间、并购关系）与第三方情报。
5. 论文由此提炼出告警应具备的五个属性：Reliable、Explainable、Analytical、**Contextual**、Transferable。

## 本课题可迁移的机制

- 这是「**实体级是可处置告警单元**」在人因侧的直接依据：分析员验证一条告警的方式，
  就是把它绑定到某个资产并调取该资产的上下文。停留在流层面的判定无法提供这一绑定。
- 「告警预算由人工复核能力决定」这一提法在本文中有定性支撑（A1、C5、G19 的表述），
  可与 Hopper（<9 条/天）、BAYWATCH（26 条/天）、Zhang 2023（10 条/天）的定量数字配合使用。

## 不可直接声称的内容

- 本文是**定性研究**，没有给出「每天多少条告警」的统计分布，也没有做流粒度与实体粒度的对照实验。
  不得用它证明任何量化的告警量比值。
- 受访者说的「99%」是**个人经验估计**，不是测量值；论文本身也明确指出这 99% 主要是良性触发。
  引用时必须写明是受访者陈述，不得写成「文献报告 SOC 误报率为 99%」。

## 仍需实验验证的假设

- 本课题 LSPR24 上「同一 4% 假阳工作点，逐流 788,295 条 vs 实体级 1,855 个」的比值
  是否落在真实 SOC 可承受区间，本文不能回答，需要另找带有「每分析员每天可处置告警数」测量的来源。
