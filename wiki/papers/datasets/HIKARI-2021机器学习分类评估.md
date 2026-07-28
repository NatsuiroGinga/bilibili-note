---
title: "使用 HIKARI-2021 数据集的网络入侵流量包分类：机器学习算法研究"
authors:
  - Rui Fernandes
  - Nuno Lopes
year: 2022
date: 2026-07-22
journal: "2022 年第 10 届数字取证与安全国际研讨会（ISDFS）"
source_pdf: "[[raw/papers/Network_Intrusion_Detection_Packet_Classification_with_the_HIKARI-2021_Dataset_a_study_on_ML_Algorithms.pdf]]"
doi: "10.1109/ISDFS55398.2022.9800807"
tags:
  - 网络安全
  - 恶意流量检测
  - 数据集
  - HIKARI-2021
  - 特征选择
  - 传统机器学习
  - 类型/论文
aliases:
  - Fernandes2022-HIKARI分类
  - HIKARI-2021 分类评估
key_finding: "该二次评估在随机打乱的80/20划分上发现KNN和随机森林使用22个卡方筛选特征仍可保持高准确率，但论文未公布22个字段名，也未执行会话或时间切分；其结果不能直接证明未知攻击或时间泛化。"
method: "卡方特征选择，KNN、MLP、SVM和随机森林，全量、半量与类别平衡数据对照"
baseline: "HIKARI-2021 原始论文中的KNN、MLP、SVM和随机森林结果"
related:
  - "[[GeNIS-模块化网络入侵检测数据集]]"
  - "[[恶意流量数据集引用核验]]"
---

# 使用 HIKARI-2021 数据集的网络入侵流量包分类：机器学习算法研究

> Rui Fernandes、Nuno Lopes，ISDFS 2022，5 页。

## 一句话

这篇论文证明了 HIKARI-2021 在随机行级划分下容易被 KNN 和随机森林分类，也暴露了明显的类别不平衡；它**不是 HIKARI-2021 原始数据论文**，没有公布 22 个入选特征，也没有提供足以复现时间或会话泛化的划分协议。

## 论文身份与来源核验

- 完整题名：`Network Intrusion Detection Packet Classification with the HIKARI-2021 Dataset: a study on ML Algorithms`。
- 作者：Rui Fernandes、Nuno Lopes，葡萄牙 IPCA 技术学院与 2AI 实验室。
- 会议：2022 年第 10 届数字取证与安全国际研讨会（ISDFS）。
- DOI：<https://doi.org/10.1109/ISDFS55398.2022.9800807>。
- 本地 PDF SHA-256：`8543e429516f9ffea137b1be663048c9b64f1a33e68e3e6d35d6ddcf00880d7e`。
- PDF 共 5 页，5 页均已逐页读取；题名、作者和 DOI 见 PDF 第 1 页。

本文在参考文献 [4] 中明确引用 Ferriyan 等 2021 年原始数据论文。因此，本文属于**二次分类与特征选择研究**，不能替代以下原始来源：

> Andrey Ferriyan、Achmad Husni Thamrin、Keiji Takeda、Jun Murai，`Generating Network Intrusion Detection Dataset Based on Real and Encrypted Synthetic Attack Traffic`，`Applied Sciences`，2021，DOI：<https://doi.org/10.3390/app11177868>。

后文的拓扑、86 个官方字段和采集场景由该原始论文的图 2、表 2、表 3 和 4.1 至 4.8 节补核；当前实际 CSV 表头和时间可用性由项目服务器只读审计补核。凡不是 Fernandes 与 Lopes 论文自身事实的内容，均明确标注来源。

## 指定论文的数据描述

论文将 HIKARI-2021 概括为实验室中生成的真实背景与加密合成攻击混合数据（PDF 第 1 至 2 页）：

- 背景流量在没有过滤器或防火墙的条件下捕获，因此可能含有未被 Zeek 识别的恶意活动。
- 良性行为使用 Selenium 驱动浏览器，模拟接近人的网页访问。
- 合成攻击包括 `Bruteforce`、`Bruteforce-XML` 和 `Probing`。
- Zeek 提供两个标签：`traffic_category` 表示类别名，`Label` 中 0 表示良性、1 表示攻击。
- 论文使用 555,278 条记录，并称数据包含 83 个特征。

PDF 第 2 页图 1 给出的近似类别比例为：`Benign` 0.63、`Background` 0.31、`Probing` 0.04，其余三类各约 0.01。精确计数应使用原始论文表 2 或真实 CSV，而不是从饼图反推。

## 原始数据论文补充核验

### 网络拓扑

指定分类论文没有重画拓扑。Ferriyan 等原始论文图 2 与 4.1 节说明：

| 网络       | 机器 | 系统与角色                                                                 |
| ---------- | ---- | -------------------------------------------------------------------------- |
| 攻击者网络 | 2 台 | CentOS 7、CentOS 8，运行 Bash 与 Python 攻击脚本                           |
| 受害者网络 | 3 台 | Debian 8 上的 Joomla 3.4.3；两台 Debian 9 上的 Drupal 8.0 与 WordPress 5.0 |

攻击者与受害者位于分离网络。受害机同时承担背景流量采集和 CMS 目标。原始论文未把交换机队列、链路容量、排队时延或拥塞状态作为数据字段，因此 HIKARI 不能直接提供 PINN 所需的队列真值。

### 正常与攻击场景

Ferriyan 等原始论文 4.2 至 4.5 节给出以下过程：

1. 背景流量来自受害者网络，不部署过滤器或防火墙；随后用 Crypto-PAn 类算法匿名化 IP 和负载敏感信息。
2. 良性配置使用无头 Chrome 与 Firefox，通过 Selenium 随机点击、注册、登录、发文和退出，并加入随机延迟与用户代理；合成良性流量使用 HTTPS。
3. 浏览器暴力破解针对 CMS 登录页。
4. `Bruteforce-XML` 通过 XML-RPC 使用不同攻击向量。
5. `Probing` 使用 `droopescan` 与 `joomscan` 扫描 WordPress、Drupal 和 Joomla 漏洞。
6. 2021-03-28 至 2021-05-04 非连续采集，每次 3 至 5 小时；依次包含仅背景、两天暴力破解、XML-RPC 暴力破解和漏洞探测场景。
7. `tcpdump` 保存完整 PCAP；Zeek 和 Python 工具完成流提取与标注。

原始论文表 5 报告总采集时长为 39 小时、7,991 个唯一 IP 地址、4 个攻击类别和 86 个正式字段。

### 标签与精确分布

原始论文表 2与服务器 CSV 审计一致：

| `traffic_category`    | 二元语义 |    流数 | 加密会话数 |
| --------------------- | -------- | ------: | ---------: |
| `Background`          | 良性背景 | 170,151 |     36,782 |
| `Benign`              | 合成良性 | 347,431 |    116,309 |
| `Bruteforce`          | 攻击     |   5,884 |      5,884 |
| `Bruteforce-XML`      | 攻击     |   5,145 |      5,145 |
| `Probing`             | 攻击     |  23,388 |     23,388 |
| `XMRIGCC CryptoMiner` | 攻击     |   3,279 |          0 |

`XMRIGCC CryptoMiner` 是作者用 Zeek 规则在背景流量验证阶段发现并单列的真实恶意加密货币挖矿流量。二元 `Label` 的实际分布为 0 共 517,582 条、1 共 37,696 条，恶意比例约 6.79%。

## 字段数量为什么出现 83、86 和 88

三个数字对应不同口径：

1. Fernandes 与 Lopes 在 PDF 第 2 页称其建模表有 **83 个特征**，但没有说明具体删除了哪三列，也没有公布最终列清单。
2. Ferriyan 等原始论文表 3 列出 **86 个正式字段**，其中前 84 个是流观测或元数据，最后两个是标签。
3. 服务器当前 `ALLFLOWMETER_HIKARI2021.csv` 实测有 **88 列**，比官方表多一个空列名和一个 `Unnamed: 0`，均为序列化索引产物，不是网络特征。

因此，不能把“83 特征”当作当前 CSV 的完整字段数，也不能在不知道列清单的情况下复现该论文的 22 特征模型。

## 当前 CSV 的完整 88 列

以下顺序来自当前官方归档内 CSV 的只读表头；第 1 列名称确实为空：

```text
01 ""
02 Unnamed: 0
03 uid
04 originh
05 originp
06 responh
07 responp
08 flow_duration
09 fwd_pkts_tot
10 bwd_pkts_tot
11 fwd_data_pkts_tot
12 bwd_data_pkts_tot
13 fwd_pkts_per_sec
14 bwd_pkts_per_sec
15 flow_pkts_per_sec
16 down_up_ratio
17 fwd_header_size_tot
18 fwd_header_size_min
19 fwd_header_size_max
20 bwd_header_size_tot
21 bwd_header_size_min
22 bwd_header_size_max
23 flow_FIN_flag_count
24 flow_SYN_flag_count
25 flow_RST_flag_count
26 fwd_PSH_flag_count
27 bwd_PSH_flag_count
28 flow_ACK_flag_count
29 fwd_URG_flag_count
30 bwd_URG_flag_count
31 flow_CWR_flag_count
32 flow_ECE_flag_count
33 fwd_pkts_payload.min
34 fwd_pkts_payload.max
35 fwd_pkts_payload.tot
36 fwd_pkts_payload.avg
37 fwd_pkts_payload.std
38 bwd_pkts_payload.min
39 bwd_pkts_payload.max
40 bwd_pkts_payload.tot
41 bwd_pkts_payload.avg
42 bwd_pkts_payload.std
43 flow_pkts_payload.min
44 flow_pkts_payload.max
45 flow_pkts_payload.tot
46 flow_pkts_payload.avg
47 flow_pkts_payload.std
48 fwd_iat.min
49 fwd_iat.max
50 fwd_iat.tot
51 fwd_iat.avg
52 fwd_iat.std
53 bwd_iat.min
54 bwd_iat.max
55 bwd_iat.tot
56 bwd_iat.avg
57 bwd_iat.std
58 flow_iat.min
59 flow_iat.max
60 flow_iat.tot
61 flow_iat.avg
62 flow_iat.std
63 payload_bytes_per_second
64 fwd_subflow_pkts
65 bwd_subflow_pkts
66 fwd_subflow_bytes
67 bwd_subflow_bytes
68 fwd_bulk_bytes
69 bwd_bulk_bytes
70 fwd_bulk_packets
71 bwd_bulk_packets
72 fwd_bulk_rate
73 bwd_bulk_rate
74 active.min
75 active.max
76 active.tot
77 active.avg
78 active.std
79 idle.min
80 idle.max
81 idle.tot
82 idle.avg
83 idle.std
84 fwd_init_window_size
85 bwd_init_window_size
86 fwd_last_window_size
87 traffic_category
88 Label
```

其中第 3 至 88 列与原始论文表 3 的 86 个字段一一对应。

## 字段含义与单位边界

| 字段族       | 字段                                                                                                         | 含义与可确认单位                                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| 序列化索引   | 空列、`Unnamed: 0`                                                                                           | 文件导出产物，无网络语义，不得输入模型                                                                                             |
| 标识与端点   | `uid`、`originh`、`originp`、`responh`、`responp`                                                            | 流标识、源/目的地址和端口；无物理单位，存在环境记忆风险                                                                            |
| 持续时间     | `flow_duration`                                                                                              | 单流持续时间；论文未声明单位，也不是绝对时间戳                                                                                     |
| 包计数       | `fwd_pkts_tot`、`bwd_pkts_tot`、`fwd_data_pkts_tot`、`bwd_data_pkts_tot`                                     | 正向/反向包数，单位为包                                                                                                            |
| 包速率       | `fwd_pkts_per_sec`、`bwd_pkts_per_sec`、`flow_pkts_per_sec`                                                  | 包/秒                                                                                                                              |
| 上下行比例   | `down_up_ratio`                                                                                              | 无量纲比值                                                                                                                         |
| 头部尺寸     | 六个 `*_header_size_*`                                                                                       | 正向/反向头部总、最小、最大尺寸；论文未逐项声明单位                                                                                |
| TCP 标志     | `FIN`、`SYN`、`RST`、`PSH`、`ACK`、`URG`、`CWR`、`ECE` 计数                                                  | 标志事件次数                                                                                                                       |
| 负载尺寸     | 15 个 `*_pkts_payload.*`                                                                                     | 正向、反向和全流负载的最小、最大、总计、均值、标准差；当前适配器按字节处理，论文没有独立单位列                                     |
| 到达间隔     | 15 个 `*_iat.*`                                                                                              | 正向、反向和全流间隔的最小、最大、总计、均值、标准差；当前项目实测确认 `flow_iat.avg` 以微秒解释，其余字段未逐项完成来源级单位核验 |
| 负载字节速率 | `payload_bytes_per_second`                                                                                   | 字节/秒                                                                                                                            |
| 子流         | `fwd_subflow_pkts`、`bwd_subflow_pkts`、`fwd_subflow_bytes`、`bwd_subflow_bytes`                             | 双向子流包数与字节数                                                                                                               |
| 批量传输     | `fwd_bulk_bytes`、`bwd_bulk_bytes`、`fwd_bulk_packets`、`bwd_bulk_packets`、`fwd_bulk_rate`、`bwd_bulk_rate` | 双向批量字节、包数和速率；速率分母及单位未由本论文明确说明                                                                         |
| 活动与空闲   | 五个 `active.*`、五个 `idle.*`                                                                               | 活动/空闲时段的最小、最大、总计、均值、标准差；论文未声明单位                                                                      |
| TCP 窗口     | `fwd_init_window_size`、`bwd_init_window_size`、`fwd_last_window_size`                                       | 初始与最后窗口尺寸；论文未声明单位                                                                                                 |
| 标签         | `traffic_category`、`Label`                                                                                  | 六类字符串标签和二元标签，不得进入观测输入                                                                                         |

**单位纪律**：字段名能支持计数、比值和每秒速率的基本解释，但两篇 HIKARI 论文都没有给出完整单位字典。正式论文只能把已由数据关系或实现核验的 `flow_iat.avg` 写成微秒，不能把所有时间字段、头部、窗口或 bulk rate 的单位一并补猜。

## 特征选择与模型协议

论文先检查相关性，随后使用卡方检验选择前 `k` 个特征。在 KNN 与随机森林上，`k=22` 时准确率约为 99%，作者据此固定 22 个特征（PDF 第 2 至 3 页、图 2 至 3）。论文没有给出这 22 个字段名、选择分数或训练折内拟合过程。

实验流程（PDF 第 3 页）：

- 先打乱全表；
- 按 80%/20% 拆分训练与测试；
- 模型为 KNN、MLP、SVM、随机森林；
- 指标为准确率、平衡准确率、精确率、召回率、F1 和训练时间；
- 环境为 i7-8750H、16 GB 内存、GTX 1050 Ti 4 GB、Python 3.10、scikit-learn 1.1.0。

论文没有说明随机种子，也没有按捕获日期、会话、端点或攻击场景分组。若卡方选择在全数据上完成后再拆分，还可能存在特征选择窥视测试集的风险；原文措辞不足以确认具体调用顺序，因此这里只标记为**待复现风险**，不直接断言已泄漏。

## 主要实验结果

### 全量数据的 83 与 22 特征比较

| 模型     | 特征数 | 准确率 | 平衡准确率 |   F1 |
| -------- | -----: | -----: | ---------: | ---: |
| KNN      |     83 |   0.98 |       0.97 | 0.98 |
| KNN      |     22 |   0.97 |       0.95 | 0.97 |
| MLP      |     83 |   0.90 |       0.61 | 0.89 |
| MLP      |     22 |   0.63 |       0.17 | 0.48 |
| SVM      |     83 |   0.92 |       0.44 | 0.91 |
| SVM      |     22 |   0.57 |       0.53 | 0.49 |
| 随机森林 |     83 |   1.00 |       1.00 | 1.00 |
| 随机森林 |     22 |   1.00 |       1.00 | 1.00 |

数据来自 PDF 第 3 页表 I。22 特征只对 KNN 与随机森林保持稳定，不能概括为所有模型都保留 99% 性能。

### 类别平衡子集

| 模型     | 每类样本数 | 准确率 | 平衡准确率 |   F1 |
| -------- | ---------: | -----: | ---------: | ---: |
| KNN      |      1,500 |   0.86 |       0.86 | 0.85 |
| KNN      |        750 |   0.82 |       0.82 | 0.82 |
| MLP      |      1,500 |   0.77 |       0.77 | 0.72 |
| MLP      |        750 |   0.58 |       0.56 | 0.54 |
| SVM      |      1,500 |   0.34 |       0.34 | 0.29 |
| SVM      |        750 |   0.16 |       0.16 | 0.07 |
| 随机森林 |      1,500 |   0.86 |       0.86 | 0.85 |
| 随机森林 |        750 |   0.86 |       0.86 | 0.85 |

数据来自 PDF 第 4 页表 III。作者指出，为适配最小类而平衡后只使用全部数据约 1.2%，并拒绝简单过采样以避免过拟合。

## 数据泄漏、类别不平衡与时间泛化风险

### 论文原文能够确认

- 数据高度不平衡，最大类别约 34.7 万条，`XMRIGCC CryptoMiner` 只有 3,279 条。
- 随机打乱后采用 80%/20% 行级划分。
- 22 个选择特征名称没有公开。
- 背景网络未部署过滤器或安全设备，Zeek 可能漏掉未知恶意流量（PDF 第 4 页）。

### 本课题推断

1. 同一捕获会话、端点、网站和攻击脚本可能同时进入训练与测试，使随机行级高分高估时间与环境泛化。
2. 地址与端口是人工标注规则的一部分，若作为输入会形成标签捷径。
3. `uid` 全部唯一，不能提供连续窗口；两个索引列也不能作为时间。
4. 当前 CSV 没有绝对时间戳，`flow_duration` 只是单流持续时间，无法恢复论文所述的 3 至 5 小时捕获会话边界。
5. 随机森林的 1.00 分数更像是域内可分性门槛，不是未知攻击、跨时间或跨场景能力证据。

## 与 GeNIS 及任务十七公共观测接口比较

### 可派生的五字段工程接口

| 统一字段             | GeNIS                | HIKARI                                        | ns-3                      | 语义问题                            |
| -------------------- | -------------------- | --------------------------------------------- | ------------------------- | ----------------------------------- |
| `total_packets`      | `TotPkts`            | `fwd_pkts_tot + bwd_pkts_tot`                 | `qdisc_received_packets`  | 公开数据按双向流，ns-3 按瓶颈窗口   |
| `total_bytes`        | `TotBytes`           | `fwd_pkts_payload.tot + bwd_pkts_payload.tot` | `qdisc_received_l3_bytes` | 事务字节、负载字节、L3 字节口径不同 |
| `packet_length_mean` | `TotBytes / TotPkts` | `flow_pkts_payload.avg`                       | L3 字节/接收包数          | 总包长、负载均值、L3 均值不同       |
| `packet_rate`        | `Rate`               | `flow_pkts_per_sec`                           | 接收包数/0.1 秒           | 流持续期速率与固定窗口速率不同      |
| `byte_rate`          | `Load / 8`           | `payload_bytes_per_second`                    | L3 字节/0.1 秒            | 事务、负载和 L3 字节层不同          |

这五个名称能构造同形张量，但当前**严格物理语义交集为空**。包数至少量纲相同，统计对象仍不同；字节和包长还存在协议层差异。任务十七必须先统一聚合对象、窗口和字节层口径，再讨论状态辨识。

### 当前五字段接口舍弃的信息

| 数据源 | 被舍弃但可能有用的信息                                                                                                  |
| ------ | ----------------------------------------------------------------------------------------------------------------------- |
| GeNIS  | 起止时间和流序列、双向包/字节/速率、到达间隔与抖动、活动/空闲、损失/重传/缺口、TCP 标志/握手/窗口、协议状态和连接上下文 |
| HIKARI | 双向包数与速率、数据包计数、头部尺寸、TCP 标志、负载最小/最大/标准差、双向到达间隔、子流、批量传输、活动/空闲、TCP 窗口 |
| ns-3   | 容量、队列锚点、到达/离开/丢弃通量、队列策略、时延和丢包配置；这些是监督真值或环境目标，不能伪装成公开推理输入          |

GeNIS 还能用 `FlowID`、`StartTime`、`LastTime` 构造受限的真实历史；当前 HIKARI 汇总 CSV 没有绝对时间戳，555,278 个 `uid` 又全部唯一，因此只能进入单窗口域偏移诊断，不能进入四窗口性能表。

## 对第三章实验的直接结论

1. HIKARI 不应承担任务十七四窗口状态辨识证据，只能用于单窗口支持范围与域可分性诊断。
2. 不复用本文随机 80/20 分数作为正式基线；若使用 HIKARI，必须至少按可恢复的捕获会话重新处理 PCAP，否则明确标为次级证据。
3. 不能引用“22 特征足够”来证明当前五字段足够，因为论文没有给出 22 个字段名，且 MLP、SVM 在 22 特征下大幅退化。
4. HIKARI 的方向、TCP 状态、波动和活动/空闲字段应作为扩展观测候选，但需要先解决时间和单位问题。
5. 地址、端口、`traffic_category`、`Label`、空索引列和 `Unnamed: 0` 不得进入状态估计器。
6. 五字段接口只能作为最小诊断对照；若无法超过常数状态下界，不能继续向 Qwen 注入所谓物理状态。

## 原始摘要要点

作者以 HIKARI-2021 为对象，比较多种传统机器学习模型并用卡方检验压缩特征；其主要结论是 KNN 和随机森林在减少特征后仍保持高域内准确率，而类别平衡后性能显著下降。该段为 PDF 第 1 页摘要的中文转述。

## 文献信息

- 本文 DOI：<https://doi.org/10.1109/ISDFS55398.2022.9800807>
- HIKARI 原始数据论文：<https://doi.org/10.3390/app11177868>
- 官方数据版本参考：<https://doi.org/10.5281/zenodo.6463389>
- 建议引用：FERNANDES R, LOPES N. Network intrusion detection packet classification with the HIKARI-2021 dataset: a study on ML algorithms[C]//2022 10th International Symposium on Digital Forensics and Security. IEEE, 2022. DOI:10.1109/ISDFS55398.2022.9800807.
