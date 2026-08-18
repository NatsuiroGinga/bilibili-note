---
title: "C2 Beaconing Detection via AI-Based Time-Series Analysis"
authors:
  - Jeetesh Gupta
  - Jan Pfeifer
  - Anum Talpur
  - Mathias Fischer
year: 2025
date: 2026-08-12
journal: "ARES 2025（LNCS 15993, pp. 409–419）"
source_pdf: "[[raw/papers/attack-detection/encrypted/2025-Gupta-C2-Beaconing-Time-Series-ARES.pdf]]"
doi: "10.1007/978-3-032-00627-1_20"
tags:
  - 恶意流量检测
  - C2信标检测
  - 时序分析
  - 实体级评价
  - 类型/论文
aliases:
  - Gupta2025-C2BeaconingTimeSeries
  - C2信标时序检测-汉堡大学
key_finding: "在含 9 台注入 Sliver C2 设备的真实企业流量上，TimeGPT-1 报出 95.6% 准确率、MVTSTrans 91.7%、LSTM 78.9%，而 BAYWATCH 与 Global Analysis 仅 13.9%/20.8%；但全文没有报告 9 台设备中检出几台，也未给出划分协议、种子与类别分布，且表 2/表 3 共 20 行中 16 行的 F1 与自身 P/R 数学不自洽。"
method: "CICFlowMeter 80+ 特征精简为时间/端口/协议/包四组，MAD 与 Bowley 偏度做周期性刻画，检测端用双向 LSTM、sktime MVTSTransformerClassifier 与 TimeGPT-1 基础模型。"
baseline: "Global Analysis（Zhang 2023 ACSAC）与 BAYWATCH（Hu 2016 DSN）两种传统信标周期性方法。"
---

# C2 Beaconing Detection via AI-Based Time-Series Analysis

> Gupta、Pfeifer、Talpur、Fischer（汉堡大学），ARES 2025 · LNCS 15993 · 第 409–419 页 · 11 页

## 一句话

这是一篇把 LSTM / MVTS Transformer / TimeGPT-1 套到 C2 信标检测上的经验性对比短文；它最有价值的部分不是那些 90%+ 的数字，而是它握着"真实企业流量 + 9 台已知注入 Sliver C2 设备"这样天然适合实体级评价的素材，却只报了样本级 accuracy/precision/recall/F1，恰好把方向 1 想填的空白暴露出来。

## 原件与来源

- 本地原件：`raw/papers/attack-detection/encrypted/2025-Gupta-C2-Beaconing-Time-Series-ARES.pdf`
- SHA-256：`663e489f20d7bf936d3d53467ddb7beb35f7785578b8b40e5e65b2c81bc51738`
- 抽取来源：`raw/papers/proceedings/2025-ARES-LNCS15993-Proceedings-Part-II.pdf` 第 423–433 页。已核验：卷内第 423 页首行为本文标题与作者，第 433 页页眉为印刷页码 419（`pdftotext -f 423/-f 433` 实测）。
- PDF 物理页 1–11 对应印刷页 409–419（`pdfinfo` 报 11 页；`pdftotext -f 6` 页眉为 414，`-f 8` 为 416，`-f 9` 为 417）。

## 任务定义与系统结构

- 任务：从网络流/日志中识别 C2 信标（beaconing）通信，即被感染主机对 C2 服务器的周期性回连（§1，印刷页 409–410）。
- 三段式系统（§3.1，印刷页 411–412，Fig. 1）：
  1. **时间特征抽取模块**：把日志压成时间属性、端口、包指标；
  2. **周期性检测模块**：用 Median Absolute Deviation 与 Bowley Skewness Measure 把节律信号与常规流量分开；
  3. **检测模块**：RNN 与 Transformer 类模型输出判定。
- 重要边界：周期性模块只在 §3.1 被点名，全文**没有对 MAD / Bowley 偏度做任何单独消融或参数说明**，也没给出它与后续深度模型的接口形式。

## 特征工程

- 原始特征用 CICFlowMeter 从 PCAP 抽取"80+ 行为指标"，另有两类数据源直接把二进制流文件/日志合并成统一 CSV（§3.2，印刷页 412）。
- 随后精简为四组（§3.2，印刷页 412）：
  - **时间特征**：year、month、day、hour、minute、second；
  - **端口特征**：源端口、目的端口；
  - **协议信息**：协议类型；
  - **包信息**：平均前向包数、平均包大小。
- 预处理：十六进制端口转十进制、列名统一，`ColumnTransformer` + `StandardScaler` + `OneHotEncoder`。
- 注意：正文特征清单里**没有 IP**，但第 4.2 节的消融却有 "No IP" 一档并说明去掉 IP 后召回从 1.00 掉到 0.85（印刷页 417），说明实际输入包含 IP 类特征而 §3.2 未列出。

## 模型

| 模型 | 关键配置 | 出处 |
| --- | --- | --- |
| LSTM | 两层双向 LSTM，各 64 单元；BatchNorm；Dropout 0.5；Dense + softmax；Adam + sparse categorical crossentropy；早停 | §3.3，印刷页 413 |
| MVTSTransformerClassifier（MVTSTrans） | sktime 实现的多变量时序 Transformer，多头注意力 + 位置编码，末端全连接 + softmax | §3.3，印刷页 413 |
| TimeGPT-1 | 编码器-解码器时序基础模型，残差连接 + 层归一化 + 局部位置编码 | §3.3，印刷页 413–414 |
| Global Analysis | Zhang et al., ACSAC 2023，聚合式跨校园网信标检测 | 参考文献 [21] |
| BAYWATCH | Hu et al., DSN 2016，大规模企业网鲁棒信标检测 | 参考文献 [9] |

关于 TimeGPT-1 的"1000 亿数据点、NVIDIA A10G 集群、数天训练"（印刷页 414）描述的是该基础模型自身的预训练规模（引自 [7]），不是本文作者的训练；本文未说明对 TimeGPT-1 做了微调、提示还是仅调用其异常检测接口。

## 数据集

Table 1（印刷页 414）：

| 数据集 | 来源 | 数据形态 | 规模 | 相关性描述 |
| --- | --- | --- | --- | --- |
| CSE-CIC-IDS2018 | CIC and CSE | Packet Captures | 16M+ records | Labeled botnet C2 traffic |
| CTU-13 | Czech Technical University | NetFlow | 2.8M+ flows | Real botnet C2 scenarios |
| Aposemat IoT-23 | Stratosphere Lab | Packet Logs | 325M+ packets | IoT-specific C2 activity |
| Real-World Data | Company's SOC Team | Anonymized Logs | 90M+ flows | Multi-variate C2 activity |

- 真实数据来自项目伙伴企业（致谢中为 DCSO GmbH，印刷页 418），其中**注入了 9 台使用 Sliver C2 的恶意信标设备**（§4.1，印刷页 415）。
- 公开集只说"抽取了代表 C2 信标行为的特定场景"（僵尸网络场景 / 各类 botnet 场景 / C2 恶意通信场景），**未给出场景清单、抽取后的样本数与良恶比例**（§4.1，印刷页 414–415）。

## 关键指标（含出处位置）

### Table 2：三个公开数据集（印刷页 416）

| 数据集 | 模型 | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| CSE-CIC-IDS2018 | Global Analysis | 42.6% | 39.8% | 37.7% | 39.8% |
| CSE-CIC-IDS2018 | BAYWATCH | 35.9% | 33.8% | 33.5% | 34.6% |
| CSE-CIC-IDS2018 | LSTM | 97.3% | 96.6% | 96.4% | 97.1% |
| CSE-CIC-IDS2018 | TimeGPT-1 | 99.7% | 99.8% | 99.4% | 99.3% |
| CSE-CIC-IDS2018 | MVTSTrans | 97.5% | 96.1% | 96.1% | 97.2% |
| CTU-13 | Global Analysis | 42.8% | 39.6% | 37.9% | 40.1% |
| CTU-13 | BAYWATCH | 35.7% | 33.6% | 33.8% | 34.9% |
| CTU-13 | LSTM | 96.9% | 95.3% | 96.0% | 96.6% |
| CTU-13 | TimeGPT-1 | 99.6% | 99.3% | 99.1% | 99.4% |
| CTU-13 | MVTSTrans | 92.7% | 91.4% | 90.7% | 92.0% |
| IoT-23 | Global Analysis | 31.4% | 30.9% | 29.2% | 30.5% |
| IoT-23 | BAYWATCH | 25.7% | 24.2% | 24.9% | 24.0% |
| IoT-23 | LSTM | 79.4% | 81.0% | 79.6% | 78.1% |
| IoT-23 | TimeGPT-1 | 95.6% | 95.3% | 95.2% | 95.4% |
| IoT-23 | MVTSTrans | 93.6% | 92.8% | 92.3% | 93.5% |

### Table 3：真实企业数据（印刷页 417）

模型在 CSE-CIC-IDS2018 上预训练后直接评估于真实数据（§4.2 小标题 "Performance of the Pre-trained Models on the Real-World Data"，印刷页 416–417）。

| 模型 | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| Global Analysis | 20.8% | 19.3% | 18.7% | 18.9% |
| BAYWATCH | 13.9% | 13.4% | 12.7% | 13.2% |
| LSTM | 78.9% | 78.2% | 77.4% | 78.3% |
| TimeGPT-1 | 95.6% | 94.8% | 94.3% | 94.9% |
| MVTSTrans | 91.7% | 90.1% | 90.0% | 91.1% |

### Fig. 2 / Fig. 3：真实数据上的特征组消融（印刷页 417）

柱状图标注值已在渲染图（`pdftoppm -f 9`）中逐柱核对，与正文数字一致。

| 特征集 | Precision（Fig. 2） | Recall（Fig. 3） |
| --- | --- | --- |
| All features | 0.96 | 1.00 |
| No IP | 0.92 | 0.85 |
| Only TS and Proto | 0.98 | 0.62 |
| Only TS | 0.94 | 0.64 |

图中未标注这是哪个模型，正文只写 "a C2 beaconing detection model"。

### 结论节复述（印刷页 418）

TimeGPT-1 95.6%、MVTSTrans 91.7%、LSTM 78.9%、Global Analysis 20.8%，即结论节直接引用真实数据这一列作为总结论。

## 审计发现：表内 F1 与自身 P/R 数学不自洽

以下是本课题的核对计算，不是论文结论。F1 = 2PR/(P+R) 必须落在 [min(P,R), max(P,R)] 内。对 Table 2 与 Table 3 全部 20 行逐行重算（输入为上两张表的 P/R/F1）：

- **16/20 行违反该区间约束**，即报告的 F1 不可能由同行的 P/R 得出。
- **20/20 行的报告 F1 与由 P/R 重算的 F1 偏差超过 0.05 个百分点**，即没有一行严格自洽。
- 典型例：CSE-CIC-IDS2018 LSTM 报 P=96.6、R=96.4、F1=97.1，重算应为 96.50，报告值高于两者；同表 MVTSTrans 报 P=R=96.1 而 F1=97.2（P=R 时 F1 必等于该值）；IoT-23 LSTM 报 P=81.0、R=79.6、F1=78.1，重算应为 80.29，报告值低于两者；真实数据 TimeGPT-1 报 P=94.8、R=94.3、F1=94.9，重算应为 94.55。
- 仅 4 行在区间意义上未违反：CSE-CIC-IDS2018 Global Analysis、IoT-23 Global Analysis、真实数据 Global Analysis、真实数据 BAYWATCH；但这 4 行的 F1 数值同样与重算值不符（如 CSE-CIC-IDS2018 Global Analysis 报 39.8，重算 38.72）。

这不推翻模型排序，但意味着**表中的 F1 列不能被直接引用为可复现指标**，也说明该文没有做基本的指标一致性检查。

## 作者自陈的局限（原样记录）

全文没有独立的 Limitations 节。作者在正文中自陈的限制只有以下几处：

- LSTM "effectively detecting short-term C2 beaconing patterns but with increased false negatives for longer sequences due to a trade-off in detection capability"（印刷页 416）。
- TimeGPT-1 "excelling in anomaly detection over extended periods but with slightly lower precision due to a higher false positive rate from its forecasting bias"（印刷页 416）。
- MVTSTransformerClassifier "closely followed TimeGPT-1 with strong performance but was limited by training constraints"（印刷页 416）。
- LSTM "showed moderate proficiency in sequential data modeling but lacked the precision of Transformer-based models, particularly for long-term dependencies"（印刷页 416–417）。
- Global Analysis 与 BAYWATCH "performed poorly, overwhelmed by real-world dataset noise, rendering them impractical for C2 detection without significant improvements"（印刷页 417）——这是作者对基线的判断，不是对自身方法的限制。
- 引言中承认 "controlled experiments with simulated data are often not realistic"（印刷页 409），作为使用真实数据的理由。

## 本课题记录的未自陈缺口（审计推论）

1. **没有实体级结果**。真实数据有 9 台已知注入的 Sliver C2 设备这一天然实体真值，但全文只报样本级四指标，**从未报告 9 台中检出几台，也未报告实体级误报数**。摘要与引言反复说"detecting malicious beaconing devices"，证据却停在样本级。
2. **没有任何划分协议**。全文未出现训练/验证/测试划分比例、随机种子、重复次数、置信区间、类别分布或代码链接；只有"预训练于 CSE-CIC-IDS2018 后评估于真实数据"这一句跨集说明。
3. **身份类特征直接进入模型**。特征含年/月/日/时/分/秒与源/目的端口，消融档位又证明 IP 特征在场。对只有 9 台注入设备的真实数据，去掉 IP 后召回从 1.00 掉到 0.85，说明高召回相当程度依赖身份记忆而非信标行为。年月日这类绝对时间字段在"注入式攻击数据集"上是典型捷径。
4. **基线可信度存疑**。BAYWATCH 与 Global Analysis 在三个公开集上准确率 25.7%–42.8%，在真实数据上 13.9%/20.8%，低于二分类随机水平；全文未给出这两种方法的重实现细节、参数、周期搜索范围与阈值，无法判断这是方法本身的能力还是重实现失当。
5. **正文自相矛盾**。印刷页 417 写 "achieves a peak precision of 0.96 with 'All features'"，同段又给出 "Only TS and Proto" 为 0.98——0.98 高于所谓峰值。
6. **与"加密"无实质关系**。全文未讨论 TLS、QUIC、握手指纹或任何加密相关处理，用的是 CICFlowMeter 统计特征，属协议无关的行为检测。放在 `encrypted/` 目录是按 C2 主题归档，不能当作加密流量方法引用。
7. **完全没有 interval / jitter 扫描**。这是一篇以"周期性"为核心卖点的论文，却没有对信标间隔、抖动幅度、抖动分布做任何分层或受控网格；也没有报告不同间隔下的检出率曲线。

## 与本课题三个候选方向的关系

### 方向 1（LSPR 跨年度检测，实体级 + 固定告警预算）——强相关，作为空白证据

- 这是继 Känzig 2019 与 Gehri 2023 之后**第三个"手里有实体真值却只报流/样本级指标"的先例**，且是 2025 年 ARES 的新论文，说明该缺口在 C2 检测线上到今天仍未闭合。与前两者的区别在于：Känzig 是在 Discussion 节做了附加的服务器级实验（30 分钟窗口 12 中识别 10）、Gehri 报了主机级 33/39，而本文**连附加的实体级数字都没有**，退化得更彻底。
- 它同时提供了"跨数据集预训练→真实部署评估"的协议形状（CSE-CIC-IDS2018 训练 → 企业流量测试），与跨年度迁移在结构上同类：都是训练域与部署域分离、都要面对部署域噪声。可以在相关工作里与 LSPR23→LSPR24 并列，作为"域外部署评价缺少实体级与预算约束"的论据。
- 可直接引用的对比点：本文真实数据 90M+ flows 中只有 9 个恶意实体，样本级 accuracy 95.6% 在这种极端不平衡下几乎没有信息量；这正是"实体级 + 固定告警预算"要取代的评价单元。本课题实测的窗口召回 0.9274 对事件召回 0.5326 是同一现象的自有证据。
- **不可直接声称**：不能说本文"证明了实体级评价更好"——它根本没做实体级评价。只能作为缺口证据引用。

### 方向 2（GeNIS 八场景组隔离）——弱相关

- 同属"行/样本级随机评价导致高分"的失败模式：16M+ records 上 97%–99.7%，无组隔离、无场景留出说明。可以在论述"随机行级划分造成假饱和"时作为跨数据集的旁证之一，但本文没有 GeNIS 那样的具名场景结构，也没有提供可复现的划分，不能承担方向 2 的主证据。

### 方向 3（TQH-C2 的 48 格 interval×jitter 网格与 B/D 跨传输协议受控对）——强相关，作为反面空白

- 本文是当前 C2 信标检测线上最新的深度模型对比工作，**却完全没有把信标间隔与抖动作为可控变量**。这直接支持方向 3 的立论：现有工作只报聚合指标，不报"检出率随间隔/抖动如何衰减"的分层曲线，因此无法回答"这些模型到底在多大抖动下失效"。
- 本文点名的两个传统基线（BAYWATCH [9]、Global Analysis [21]）与周期性统计量（MAD、Bowley 偏度，即 RITA 系做法）正是 48 格网格里天然的确定性对照组：它们无需训练、计算便宜、对间隔/抖动的响应可解析，适合当作分层曲线的下界基线。
- 本文报出的基线崩溃（真实数据上 13.9%/20.8%）如果成立，恰恰说明"聚合一个数字"掩盖了机制差异——在受控网格里，这类周期性方法在低抖动格点应该很强、高抖动格点才崩，把它压成单一准确率是信息损失。这可以写成方向 3 的动机段。
- 本文未做跨传输协议（HTTP/3-over-QUIC vs HTTP/2-over-TLS）的任何分析，与方向 3 的 B/D 受控对无重叠，不能作为该子问题的先例。

## 可迁移的机制

1. **周期性统计量组合**：Median Absolute Deviation + Bowley Skewness Measure 作为轻量周期性刻画（§3.1，印刷页 411–412）。本文没做消融，但这组统计量可以在本课题的受控网格里被完整消融，填补它留下的空白。
2. **基线选型**：BAYWATCH（DSN 2016）与 Global Analysis（ACSAC 2023）是这条线公认的两个可引用对照；本文给出了引用锚点，但其复现数字不可信，需要自行实现或引用原文数字。
3. **跨域评估形状**：公开集预训练 → 真实部署域测试，且部署域含少量已知注入实体。这个形状可直接改造为"公开集训练 → LSPR24 部署 + 实体级固定预算"的评价协议。
4. **指标一致性门禁**：本次审计用的 F1∈[min(P,R), max(P,R)] 检查在 5 秒内定位了 15 行不自洽，成本极低。建议固化为本课题引用他人表格前的常规校验步骤，凡是不自洽的行一律不进入论文对比表。

## 不可直接声称的内容

- 不能引用"TimeGPT-1 在真实企业流量上达到 95.6% 准确率"来论证基础模型适用于 C2 检测：无划分协议、无种子、无置信区间、含 IP 与绝对时间特征、F1 列自相矛盾。
- 不能引用"BAYWATCH 只有 13.9% 准确率"来贬低传统周期性方法：这是无细节的第三方重实现结果，低于随机水平。
- 不能把本文当作加密流量检测工作引用。
- 不能声称本文验证了实体级检测能力；它只有实体级的数据条件，没有实体级的评价。

## 仍需验证的假设

- 若在同样的"少量注入实体 + 海量良性流"设定下改用实体级 + 固定告警预算评价，样本级 95% 与实体级检出率的差距有多大？本课题 LSPR24 上窗口召回 0.9274 对事件召回 0.5326 提示差距显著，但需要在 C2 信标设定下重测。
- MAD + Bowley 偏度在受控 interval×jitter 网格上的失效边界在哪里？这是方向 3 可以立刻跑的最小实验。
- 移除年/月/日/时/分/秒等绝对时间字段与 IP 字段后，本文这类模型还剩多少性能？本文的 "Only TS and Proto" 召回 0.62 已给出弱提示，但口径不明。

## 文献信息

- DOI：<https://doi.org/10.1007/978-3-032-00627-1_20>
- 会议：ARES 2025（20th International Conference on Availability, Reliability and Security），LNCS 15993，pp. 409–419
- 机构：University of Hamburg
- 资助：德国联邦研究、技术与航天部 Grant No. 16KISA068K；Cyberagentur SOVEREIGN 项目
- 数据致谢：DCSO GmbH 提供匿名真实数据
- 本地 PDF SHA-256：`663e489f20d7bf936d3d53467ddb7beb35f7785578b8b40e5e65b2c81bc51738`

## 相关笔记

- [[2023-Zhang-大规模校园网聚合信标检测]]：本文参考文献 [21]，即被当作 "Global Analysis" 基线的原始工作；本文报出的 20.8%–42.8% 准确率应回到该原文核对，不可替代原文数字。
- [[2019-Kanzig-LockedShields-C2信道机器学习检测]]：本文参考文献 [12]，同为"有实体真值但主指标停在流级"的先例，且其 Discussion 节做了服务器级附加实验，可与本文的完全缺失形成对比。
- [[Novo2020-加密恶意C2流量检测与代理规避]]：同为 C2 流量检测，但关注对抗规避可实现性。
- [[GeNIS-跨网络迁移评估]]：同域近饱和与跨域失败的对照证据。
