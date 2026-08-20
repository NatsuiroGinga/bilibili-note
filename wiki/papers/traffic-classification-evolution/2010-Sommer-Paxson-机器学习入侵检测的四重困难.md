---
title: "Outside the Closed World: On Using Machine Learning for Network Intrusion Detection"
authors: [Robin Sommer, Vern Paxson]
year: 2010
date: 2026-08-19
journal: "IEEE Symposium on Security and Privacy (S&P) 2010, pp. 305-316"
source_pdf: "[[raw/papers/traffic-classification-evolution/2010-Sommer-Paxson-Outside-the-Closed-World-ML-NIDS-IEEE-SP.pdf]]"
tags:
  - 入侵检测
  - 评价方法学
  - 部署困难
  - 加密恶意流量检测
  - 类型/论文
key_finding: "机器学习在网络入侵检测中学术成果多而实际部署少，根因是四项与其他 ML 应用域不同的结构性困难：需要做离群检测、错误代价高、检测结果与运维语义之间有语义鸿沟、网络流量本身多样性极大。"
method: "问题分析与方法学建议，非实验论文"
aliases:
  - Sommer2010
  - Outside the Closed World
related:
  - "[[2005-Karagiannis-BLINC黑箱多层流量分类]]"
---

# Outside the Closed World: On Using Machine Learning for Network Intrusion Detection

> Sommer & Paxson, 2010, IEEE S&P · 原件 12 页
> DOI `10.1109/SP.2010.25`

## 一句话

入侵检测不是普通分类问题；把它当普通分类问题做，是学术指标好看而部署失败的原因。

## 论文原结论（四项困难，均可定位）

原件 p.1 摘要与 §III 逐项展开：

| 困难 | 位置 | 要点 |
| --- | --- | --- |
| 需要离群检测 | §III.A（p.2 右栏起，p.3 第 10 行） | 异常检测系统必须先有"正常"的概念；而 ML 擅长的是在已知类之间划界，即**闭世界假设**（p.3 第 45 行原文点名 `closed world assumption`）。 |
| 错误代价高 | §III.B（p.3 第 69 行） | 单条误报的运维成本远高于其他领域，因此可接受的误报率极低。 |
| 语义鸿沟 | §III.C（p.4 第 7、11、32 行） | 模型判"异常"与运维需要的"这是什么攻击、要怎么处置"之间没有直接映射。 |
| 流量多样性 | §III.D（p.4 第 34 行） | 网络流量的多样性远超一般认知，"正常"本身不稳定。 |

§IV 是使用建议（p.5 第 100 行标题 `RECOMMENDATIONS FOR USING MACHINE LEARNING`），
其中 §IV.A `Understanding the Threat Model`（p.6 第 126 行）与
`1) Difficulties of Data`（p.5 第 50 行）、`2) Mind the Gap`（p.5 第 87 行）
是本课题评价协议设计的直接依据。

## 本课题用途

1. **1.2.1 段末共同短板的规范出处**：解释为什么表征做得再好，
   部署侧仍以极低误报率为硬约束。
2. **与 Arp 2022 的分工**：Arp 讲的是实验设计中的具体陷阱（可机械检查），
   Sommer & Paxson 讲的是任务本身的结构性困难（不可靠机械检查消除）。
   两者不可互相替代，本课题在 1.2.1 末段并引。
3. **与本课题实体级判定的关系（本课题推论，非论文原结论）**：
   语义鸿沟这一项支持"把判定单元上移到运维可处置的实体"，
   但论文本身没有提出实体级判定方案，引用时不得写成它支持本课题方法。

## 短板

论文是立场与方法学分析，不提供可复现的实验证据与基线；
其结论的量化版本要靠后续工作（Arp 2022、Jacobs 2022）补。
