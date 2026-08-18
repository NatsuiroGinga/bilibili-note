---
title: "Machine Learning-based Detection of C&C Channels with a Focus on the Locked Shields Cyber Defense Exercise"
authors: [Nicolas Känzig, Roland Meier, Luca Gambazzi, Vincent Lenders, Laurent Vanbever]
year: 2019
date: 2026-08-12
journal: "2019 11th International Conference on Cyber Conflict: Silent Battle（CyCon 2019），NATO CCD COE Publications，Tallinn"
source_pdf: "[[raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon.pdf]]"
source_slides: "[[raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon-SLIDES.pdf]]"
sha256_pdf: "155f49f2d1d84672"
sha256_slides: "5e6b21ff3dd26d54"
doi: "未在全文中定位（PDF 19 页正文与元数据均无 DOI/ISBN 字符串，仅有 IEEE Xplore 下载水印）"
tags:
  - 加密恶意流量检测
  - C2流量
  - LockedShields
  - 跨年度泛化
  - 随机森林
  - CICFlowMeter
  - 实体级检出
  - 类型/论文
key_finding: "LSPR 全族方法学源头：CICFlowMeter 77 特征递归消除到 20 维 + 随机森林，LS17↔LS18 交叉年度训练/测试，调优模型精确率 0.99、召回 0.98/0.90（表 IV，PDF 第 14 页，十种子中位数）；§5.A 的 30 分钟识别 12 台 C&C 服务器中的 10 台是 Discussion 节附加实验，未形式化为评价协议，也未报告实体级误报。"
method: "包截断 96 字节 + 15 秒超时的 5 元组流聚合 + CICFlowMeter 3.0 提取 77 特征 + 基于 Gini 重要度的递归特征消除取 20 维 + 随机森林（tuned：128 树、最大深度 10）。"
baseline: "scikit-learn 默认 RF（10 树、不限深度）作为 baseline 配置；模型选择阶段比较过 ANN、SVM、逻辑回归、朴素贝叶斯、KNN。"
aliases:
  - Känzig2019
  - Kanzig2019-LockedShields-C2
  - LS17/LS18 交叉年度 RF 基线
related:
  - "[[Novo2020-加密恶意C2流量检测与代理规避]]"
  - "[[Xavier2022-Metasploit加密C2规避]]"
---

# Känzig 2019：Locked Shields 演习中的 C&C 信道机器学习检测

## 一句话

这篇论文奠定了 LSPR 系列数据集的方法学基线——用往届演习数据训练、在下一届不同网络上直接测试的跨年度逐流随机森林；它同时是"实体级评价"最早的先例，但那只是 Discussion 节里的一次附加观察，既未定义协议也未报告实体级误报。

## 题录与原件

- 作者：Nicolas Känzig、Roland Meier、Laurent Vanbever（ETH Zürich），Luca Gambazzi、Vincent Lenders（armasuisse Science and Technology）（PDF 第 1 页作者块）。
- 出处：2019 11th International Conference on Cyber Conflict: Silent Battle，NATO CCD COE Publications，Tallinn，2019（PDF 第 1 页版权页）。
- 原件：`raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon.pdf`，19 页，SHA-256 前缀 `155f49f2d1d84672`。
- 同名会议幻灯片：`raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon-SLIDES.pdf`，62 页，SHA-256 前缀 `5e6b21ff3dd26d54`，PDF 元数据标题 `190529_CyCon_LS_Roland_Meier`，创建时间 2019-06-11。
- DOI：全文与 PDF 元数据中未出现 DOI 或 ISBN 字段，只有"Downloaded ... from IEEE Xplore"水印；DOI 需另行核实后补录。

## 任务定义

- 目标：在 Locked Shields 演习中，不依赖对防守网络的先验知识，识别受控主机与 C&C 服务器之间的信道，从而在攻击真正发起前定位被攻陷主机（PDF 第 3 页 Problem statement；第 3 页正文"identifying this type of traffic is fruitful because it means that compromised hosts can be identified ... before an actual attack is launched"）。
- 核心假设：良性背景流量逐年变化，但 C&C 会话特征几乎不变，因为红队每年都用同一套 Cobalt Strike 框架（PDF 第 7 页 §2.C；第 11 页 §3.E 模型选择段落明确写出这一分布差异论证）。
- 评价单元：**流**。精确率定义为"被报为 C&C 的流中真正是 C&C 流的比例"，召回定义为"正确识别的 C&C 流数 / 数据集中全部 C&C 流数"（PDF 第 13 页 §4.B 首段）。
- 部署约束：防守方只有两台 VM、低带宽 VPN、有限存储，因此不允许把大量流量送到外部系统（PDF 第 6 页 §2.B）。

## 数据集与规模

数据来自瑞士蓝队在 LS17、LS18 两届演习中记录的完整 pcap（未采样、未匿名、未截断），标注依据是 Cobalt Strike 生成的红队日志中的 IOC 列表（PDF 第 8 页 §3.B.1）。

| 数据集 | 大小 | 包数 | 流数 | C&C 流数（占比） | 出处 |
| --- | --- | --- | --- | --- | --- |
| LS17 | 114 GB | 288,940,662 | 9,070,828 | 1,239,041（13.7%） | 表 II，PDF 第 13 页 |
| LS18 | 216 GB | 557,783,930 | 16,379,346 | 1,818,006（11.1%） | 表 II，PDF 第 13 页 |

- 两个数据集各约 38 小时网络流量（表 V 标题，PDF 第 14 页）。
- 标注规则：只要流的任一端点出现在红队日志的 C&C 服务器列表中就标为恶意，其余为良性；作者的理由是"没有任何良性理由让设备联系 C&C 服务器"（PDF 第 8 页 §3.C）。
- 该标注是**端点级传递标注**，不是逐流行为判定；这一点对本课题的标签删失与事件级评价讨论直接相关。

## 方法要点

- **包截断**：每包只保留前 96 字节（到传输层头部），数据体积减少约 75%，作者称最终模型性能未因截断下降（PDF 第 8 页 §3.B.2.a）。
- **流定义**：5 元组（源 IP、目的 IP、源端口、目的端口、传输层协议）；以 TCP SYN 开始，以首个 FIN 或 15 秒超时结束（PDF 第 8 页 §3.B.2.b）。
- **特征提取工具**：CICFlowMeter 3.0，共 77 个特征，以包间隔、方向分离的活跃/空闲时间及其最小/最大/均值/标准差为主（PDF 第 8 页 §3.B.2.b 与第 9 页 §3.D.1；表 V 标题再次确认"extracts all 77 features from Table I"，PDF 第 14 页）。作者额外加了一个 `Int/Ext Dst IP` 特征，标识目的 IP 是否在内网地址空间（PDF 第 9 页 §3.D.1）。
- **域名解析**：用 Bro 从 HTTP host 头、TLS SNI 与 DNS 中把红队日志里的域名映射为 IP（PDF 第 9 页 §3.B.2.c）。
- **特征选择**：基于随机森林 Gini 重要度的递归特征消除，每轮删掉得分最低的一个特征；作者强调必须逐个删除，否则冗余相关特征会同时被压低分数（PDF 第 10 页 §3.D.2）。
- **最终 20 维特征集**（PDF 第 11 页，按重要度降序，最后两个是依据初步实验补入的）：Tot Fwd Pkts、Flow IAT Mean、Fwd IAT Max、Flow Pkts/s、Bwd Pkt Len Min、FIN Flag Cnt、Init Fwd Win Byts、Active Mean、Bwd IAT Mean、Bwd Pkt Len Std、Fwd Seg Size Min、Fwd Pkt Len Std、Tot Bwd Pkts、Bwd Header Len、Subflow Fwd Byts、Subflow Bwd Pkts、Fwd IAT Tot、Flow IAT Max、Int/Ext Dst IP、L3/L4 Protocol。
- **模型**：比较 ANN、SVM、逻辑回归、朴素贝叶斯、KNN、随机森林后选定随机森林（PDF 第 11 页 §3.E）。baseline 为 scikit-learn 默认（10 棵完全展开的树，LS17 模型约 30,000 节点、LS18 约 70,000 节点）；tuned 为最大深度 10、128 棵树，节点数降至 LS17 约 700、LS18 约 900（PDF 第 11 页 §3.E.1）。
- **交叉年度协议**：用完整 LS17 训练、完整 LS18 测试，反之亦然；作者称这对应"在不同网络上分类此前未见数据"的场景（PDF 第 13 页 §4.A.1 与表 III）。
- **规避不变性论证**：Cobalt Strike 的 sleep-period 与 jitter 只影响周期性连接之间的间隔，而本文特征全部是单连接内部的时序统计，因此对二者不变；Malleable C2 改 HTTP 头也无效，因为模型不用 HTTP 头特征（PDF 第 11–12 页 §3.E.2.a）。

## 关键指标表（带出处位置）

### 表 IV：交叉年度精确率/召回（十次随机种子取中位数）

| 模型 | 训练 | 测试 | 精确率 | 召回 |
| --- | --- | --- | --- | --- |
| LS17-baseline | LS17 | LS18 | 0.94 | 0.98 |
| LS17-tuned | LS17 | LS18 | 0.99 | 0.98 |
| LS18-baseline | LS18 | LS17 | 0.98 | 0.86 |
| LS18-tuned | LS18 | LS17 | 0.99 | 0.90 |

出处：表 IV，PDF 第 14 页（pdftotext 第 604–633 行）。训练/测试映射见表 III，PDF 第 13 页。"We repeated the evaluation ten times with different random seeds to train the models, and we report the medians of the results"——PDF 第 13 页 §4.B 第二段（pdftotext 第 600–602 行）。论文只报中位数，未给分位数、方差或置信区间。

### 表 V / 表 VI：运行时

| 项 | LS17 | LS18 | 出处 |
| --- | --- | --- | --- |
| CICFlowMeter 特征提取 | 42 min（9,070,828 流） | 85 min（16,379,346 流） | 表 V，PDF 第 14 页 |
| baseline 训练 | 120 s | 390 s | 表 VI，PDF 第 15 页 |
| tuned 训练 | 1117 s | 2828 s | 表 VI，PDF 第 15 页 |
| baseline 推理（全集） | 6 s | 4 s | 表 VI，PDF 第 15 页 |
| tuned 推理（全集） | 50 s | 30 s | 表 VI，PDF 第 15 页 |

实验环境：Ubuntu 16.04 64 位虚拟机，10 个 Intel Xeon E5-2699 核，16 GB RAM，Python 3.6 + scikit-learn 0.19.2（PDF 第 13 页 §4.A.2）。

### 鲁棒性（图 3–5，只有曲线，无数值表）

- 伪装攻击建模方式：把恶意样本中被攻击特征的取值替换为从良性样本随机抽取的值，攻击者按重要度顺序攻击前 n 个特征，n 取 5–14，每点 10 个随机种子，绘制中位数与 95% 置信区间（PDF 第 15 页 §4.D）。
- 结论文字：tuned 模型在篡改超过 12 个特征时精确率才跌破 90%；LS18 模型在攻击超过 5 个特征后召回急剧下降，但精确率仍高（PDF 第 15 页 §4.D 末段）。图 3 标题写"robust against tampering, for up to 10 features"（PDF 第 15 页）。
- 丢包鲁棒性：随机丢弃 10%–90% 的包，tuned 模型在 90% 丢包下精确率仍 > 95%，召回随丢包率近似线性下降；曲线为 10 次测量的均值（PDF 第 16 页 §4.E 与图 5）。
- **具体数值未在全文中定位**：图 3、图 4、图 5 的坐标数值在 pdftotext 输出中不可读，只有图标题与正文定性描述。

### §5.A「Identifying C&C Servers」：实体级附加实验

原文（PDF 第 17 页，pdftotext 第 765–774 行）：在 LS18 演习开始阶段运行系统一段 30 分钟的短时间窗（标注为 11am–12 pm），足以识别出 Cobalt Strike 报告中列出的 **12 台 C&C 服务器中的 10 台**；同时观察到蓝队网络中有 **5 个不同源 IP** 与这些服务器通信，提示这些主机此时已被攻陷。

结论节复述（PDF 第 18 页 §6，pdftotext 第 855–858 行）：如果该队用 2017 年数据训练分类器，就能以 99% 精确率、98% 召回识别 LS18 的 C&C 信道；只运行 30 分钟就足以识别 12 台中的 10 台。摘要（PDF 第 2 页）的措辞是"would have discovered 10 out of 12 C&C servers **in the first hours** of the exercise"。

**必须记录的三个缺口：**

1. **未报实体级误报**。论文只给出 10/12 这个召回侧数字，没有给出该 30 分钟窗内被标记的不同目的 IP 总数，因此无法算出实体级精确率或告警预算。全文中不存在实体级 FP/precision 的任何数值。
2. **未形式化为评价协议**。该实验出现在 Discussion 节（§5.A）而非 Evaluation 节（§4），没有定义实体聚合规则（多少条被判恶意的流才算一台服务器被识别）、没有阈值、没有多种子重复、没有对另一年份或另一时段复现。
3. **时间窗描述自相矛盾**。§5.A 同一句里写"30 minutes"却把区间标为"11am-12 pm"（60 分钟）；摘要又写成"in the first hours"。三处表述不一致，引用时必须原样注明。

### 幻灯片中的头条句（来源为幻灯片，非论文）

幻灯片第 9 页头条：**"If the Swiss Blue Team had used our system at Locked Shields 2018, it would have discovered more than 80% of the C&C servers within 30 minutes."**（`2019-Kanzig-ML-Detection-CC-Channels-CyCon-SLIDES.pdf` 第 9 页）

- 10/12 = 83.3%，与"more than 80%"一致；但**这句话只出现在幻灯片，论文正文没有以百分比形式表述过实体级检出**。引用百分比时必须标注来源为会议幻灯片。
- 幻灯片其他与论文不完全一致的点：
  - 幻灯片第 53–55 页只展示 tuned 结果（LS17 模型 99%/98%，LS18 模型 99%/90%），略去 baseline 两行。
  - 幻灯片第 56 页给出**单流分类耗时**：LS17 模型 3.1 μs/流，LS18 模型 3.3 μs/流。该逐流微秒数在论文中未出现（论文只报全集推理秒数）。
  - 幻灯片第 57 页写"robust against tampering with up to **8** features"，而论文图 3 标题写 up to **10** features、正文写精确率在 >12 个特征时才跌破 90%。三处口径不同。
  - 幻灯片第 58–60 页报告了论文中完全没有的后续事实：瑞士蓝队在 **Locked Shields 2019** 实际部署了该系统，使用 LS17 与 LS18 训练的模型、相同特征但换了特征提取工具，观察到"很高的真阳性率、检测到未知 C&C 服务器、确认了已知 C&C 服务器"。这些是幻灯片口头汇报，无任何量化指标。
  - 幻灯片第 5 页给出演习规模：1,200 名专家、30 国、4,000 台虚拟系统、2,500 次攻击（论文第 5 页只写"more than 1000 cyber experts from 30 nations"）。

## 作者自陈局限（原样记录）

- §5.B（PDF 第 17 页）：建议未来同时并行运行多个年份训练的模型以抬高红队伪装成本，但"Since we have data from only two iterations of Locked Shields, we could not evaluate this approach"——该多模型方案**未被评估**。
- §5.D（PDF 第 18 页）：监督学习系统的主要局限是"while they are highly effective in detecting anomalies that were labeled in the training set, they fail to detect new and unknown attacks"；另一个挑战是合法背景流量的分布在不同网络间差异很大。
- §5.D：本文聚焦于一个非常特定的用例（Locked Shields + Cobalt Strike）；要迁移到其他环境需要扩充更多 C&C 流量类型与更广的合法流量画像，并提出域随机化（引用 OpenAI 机械手）作为**尚未实施**的可能路径。
- §3.E.2.b（PDF 第 12 页）：许多特征篡改本可通过特征提取阶段的额外检查（如序列号校验）防御，但作者假设防守方因计算开销做不到，因此鲁棒性实验是在"防守方无法检测注入"的前提下做的。
- §4.C（PDF 第 14 页）：承认 CICFlowMeter 提取了全部 77 个特征而非仅所需的 20 个，运行时可通过只算 20 个特征和更高效实现显著改进——即报告的 42/85 分钟不是该方法的效率下界。

## 与本课题的关系

本课题方向为加密恶意流量检测的训练方法与训练系统；四个自研 P0（跨年度迁移、有界残差、证据累积、预算分配）已全部实验否决，现转向基于他人已有工作提出改进。这篇论文是**方向 1（LSPR 跨年度检测，评价单元从逐流改为实体级 + 固定告警预算）的直接先例与改进锚点**。

- **它是 LSPR 全族的方法学源头**。本课题使用的 LSPR 系列数据、CICFlowMeter 流特征口径、5 元组 + 15 秒超时的流定义、以及"上一届训练、下一届测试"的跨年度协议，都可以追溯到这篇论文的 §3.B–§4.A。任何关于 LSPR 评价协议的讨论都必须以它为基准。
- **它已经提出了实体级观察，但没有把它做成评价协议**。这正是方向 1 的空白位置：§5.A 只给召回侧的 10/12，不给实体级误报、不给告警预算、不给聚合规则、不做多种子重复、不在其他时段或年份复现。因此"把评价单元形式化为实体级 + 固定告警预算"不是重复劳动，而是补上该文自己没有闭合的一步。
- **它的逐流指标与实体级观察之间的落差与本课题实测同构**。论文逐流召回在 LS18→LS17 方向掉到 0.90（tuned）/0.86（baseline），而 30 分钟窗内实体级检出 10/12；本课题实测窗口召回 0.9274 对事件召回 0.5326，方向相反但同样说明两种评价单元不可互相替代。引用时应说明：Känzig 的实体级数字看起来比逐流更好，是因为一台服务器只要有任意一条流被命中就算命中，而这恰恰是缺少实体级误报数据时不能自证的宽松准则。
- **与 Gehri 2023（私有数据逐流 F1 0.185、主机级 33/39）合起来构成同一现象的两个先例**：逐流指标与实体级指标可以差出一个量级。Känzig 是该现象最早的记录，Gehri 是同一实验族内的复现。
- **可迁移的机制**：
  1. 端点级传递标注（任一端点在 IOC 列表中即标恶意）——本课题若采用实体级评价，标签本身天然是实体级的，实体级 ground truth 可直接从红队 IOC 列表构造，无需额外标注。
  2. "背景流量逐年变化、C&C 特征因框架固定而稳定"的分布论证——这是跨年度泛化能成立的机制解释，可直接作为方向 1 的假设来源，但需注意它依赖红队连年使用同一 C&C 框架这一外生条件。
  3. 单连接内部时序统计对 sleep/jitter 不变——与方向 3（TQH-C2 的 interval×jitter 受控网格）形成对照：Känzig 用"我的特征对这两个参数不变"来论证鲁棒性，而 TQH-C2 提供了真正在这两个维度上做受控扫描的数据，可以对该论证做实证检验而非仅接受其文字论证。
  4. tuned 配置（限深 10、128 树）显著提高跨年度稳定性与抗篡改性——树深约束作为跨域正则化的证据，可作为本课题任何树模型基线的默认设置依据。
- **不能借用的部分**：论文没有给出任何实体级精确率、告警预算或 ROC/PR 曲线，因此不能用它的 10/12 论证"实体级评价下检测已接近解决"；也不能用它的 0.99 精确率作为实体级精确率的替代。

## 允许主张

- Känzig 2019 是 LSPR 跨年度检测的方法学源头，确立了 CICFlowMeter + 随机森林 + 交叉年度训练/测试的基线协议。
- 该文在 Discussion 节记录了实体级（C&C 服务器级）检出的可能性，但未将其形式化为评价协议，也未报告实体级误报，这构成方向 1 的明确研究空白。
- 该文的逐流指标（表 IV）与实体级观察（§5.A）之间存在评价单元不一致，与本课题实测的窗口召回/事件召回落差属于同类现象。

## 禁止主张

- 不得把"discovered more than 80% of the C&C servers within 30 minutes"当作论文正文的表述——它只出现在幻灯片第 9 页。
- 不得从 10/12 推导任何实体级精确率、误报率或告警预算数字；论文没有提供分母。
- 不得把"30 分钟"当作确定的窗口长度而不注明论文自身在 §5.A（30 minutes / 11am-12 pm）与摘要（in the first hours）之间的表述矛盾。
- 不得把表 IV 的 0.99/0.98 理解为在同一年份内划分的结果；四行全部是交叉年度设置（表 III，PDF 第 13 页）。
- 不得把幻灯片第 58–60 页的 Locked Shields 2019 实战部署结论当作论文的实验证据；那部分没有任何量化指标，也未经同行评审。
- 不得把图 3–5 的具体数值写入论文；这些数值在 pdftotext 输出中不可读，只有定性描述可用。

## 未能核实

- DOI：全文与 PDF 元数据无 DOI/ISBN 字符串，需另行核实后补录 frontmatter。
- 图 3、图 4、图 5 的坐标数值（篡改特征数—精确率/召回曲线、丢包率—精确率/召回曲线）。
- 表 I 的 77 个特征完整名称：pdftotext 只提取到编号列（Nr 1、2-3、4-5、…、77），特征名称列未被提取（PDF 第 10 页）。仅确认了 §3.D.2 中的 20 维最终特征集。
- §5.A 中被标记的目的 IP 总数、该 30 分钟窗的流量规模，以及 5 个源 IP 是否包含误报。
