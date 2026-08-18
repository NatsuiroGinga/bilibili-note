---
title: "Temporal Analysis of NetFlow Datasets for Network Intrusion Detection Systems"
authors: [Majed Luay, Siamak Layeghy, Seyedehfaezeh Hosseininoorbin, Mohanad Sarhan, Nour Moustafa, Marius Portmann]
year: 2025
date: 2026-08-13
journal: "arXiv 预印本 arXiv:2503.04404v2 [cs.LG]，2025 年 3 月 9 日；原件封面除年份 2025 外无会议或期刊信息"
source_pdf: "[[raw/papers/datasets/analog-benchmarks/2025-Temporal-Analysis-NetFlow-Datasets-NIDS-arXiv2503.04404.pdf]]"
doi: "arXiv:2503.04404"
tags:
  - NetFlow标准特征集
  - NIDS数据集
  - 时序特征
  - 到达间隔
  - 数据集刻画
  - 类型/论文
aliases:
  - Luay2025-NF3-Datasets
  - NF3-Datasets
key_finding: "把 UNSW-NB15、BoT-IoT、ToN-IoT、CSE-CIC-IDS2018 四个基准重新转换为带时序特征的 NetFlow 版本（NF3），补上了此前 NetFlow 标准特征集缺失的流起止毫秒时间戳与四类 IAT 统计（Table 1，第 6 页）；四个数据集的恶意流占比分别为 5.40%、38.98%、12.93%、99.7%（Table 2，第 9 页），其中 NF3-BoT-IoT 的良性流只有 51,989 条、占 0.3%。全文是数据刻画与可视化工作，未训练或评估任何检测模型。"
method: "nProbe（NetFlow v9，`--dont-reforge-time` 保留原始时间戳）把各数据集官方 PCAP 转成流记录，导出 57 个字段；再以精确时间戳 + 五元组与官方 ground truth 文件比对打标，生成二分类与多分类两列标签；随后做流长分布、IAT 分布、逐分钟时间序列、类别字段唯一值时间序列与谱图（时频）分析"
baseline: "无模型基线。对照对象是 Sarhan 等此前的 NetFlow 版本数据集（NF-v1/v2，43 个特征），本文在其特征集基础上追加时序特征"
related:
  - "[[2026-ElMahdaouy-上下文感知NetFlow入侵检测综述]]"
  - "[[2024-Hynek-CESNET-TLS-Year22跨年度TLS流量数据集]]"
  - "[[NIDS跨数据集泛化研究]]"
  - "[[Bad-Design-Smells-NIDS数据集设计气味]]"
---

# NetFlow NIDS 数据集的时序分析（NF3 数据集）

> Luay、Layeghy、Hosseininoorbin、Sarhan、Moustafa、Portmann（昆士兰大学与新南威尔士大学堪培拉分校一系的 NetFlow 数据集课题组）。arXiv:2503.04404v2，2025-03-09。
> 数据发布地址：`https://staff.itee.uq.edu.au/marius/NIDS_datasets/`（参考文献 1，第 19 页）。

## 一句话

这是一篇**数据刻画**论文而不是方法论文：它的实质贡献是把四个常用 NIDS 基准重新用 nProbe 转成保留原始时间戳与 IAT 统计的 NetFlow 版本，并系统展示了「这些基准的时间结构长什么样」——包括一个对本课题很有用的负面事实：多数数据集把不同攻击类别**分散在不同天**执行（Table 4，第 14 页），因此任何按时间切分的评估都会同时切掉某些类别。

## 动机与定位

- 出发点是 NetFlow 标准特征集的缺口：Sarhan 等此前把四个高被引基准统一到 43 个 NetFlow 特征，解决了特征口径不一致的问题，但**这些版本缺少大部分时序特征**，导致序列神经网络模型或基于时间的攻击刻画无从下手（第 2 页 §1）。
- 作者反复强调本文**不做分类、不与 SOTA 竞争**：目标是在特征层面理解 NetFlow 数据集的时间特性，为后续建模提供基础（第 5 页 §1 结构说明、第 9–10 页 §5 开篇）。

## NF3 数据集的构造

- 源数据：UNSW-NB15、BoT-IoT、ToN-IoT、CSE-CIC-IDS2018 的官方 PCAP。作者提到 CSE-CIC-IDS2018 一家就有 **4,000 多个 PCAP 文件、超过 400 GB**（第 7–8 页 §4.2）。
- 转换命令原样记录（第 8 页 §4.2）：

```
nprobe -i file.pcap -V 9 --dont-reforge-time -T %feature1%feature2%featureN
--dump-path <path> --dump-format t --csv-separator '#'
```

  其中 `--dont-reforge-time` 用于保留原始抓包时间戳，避免被改写成命令执行时刻；`-T` 共导出 **57 个流特征**。
- 打标：用精确时间戳 + 五元组（源/目的 IP、源/目的端口、协议）与 ground truth 文件比对，追加二分类列（0 良性 / 1 恶意）与多分类列（具体攻击类型）（第 8 页 §4.2）。
- 作者明确声明数据集内的时间戳来自原始 PCAP 而非转换时刻，以保持原始网络条件的时间完整性（第 9 页 §4.2 末）。

### 新增的时序特征（Table 1 加粗项，第 6 页）

分两类：

- **流时序（Flow Timing）**：`FLOW_START_MILLISECONDS`、`FLOW_END_MILLISECONDS`，Unix 毫秒时间戳。
- **包间到达时间（IAT）**：`SRC_TO_DST_IAT_{MIN,MAX,AVG,STDDEV}` 与 `DST_TO_SRC_IAT_{MIN,MAX,AVG,STDDEV}` 共 8 维。作者说明这些量源自包级观测但**聚合到流级**呈现（第 7 页 §4.1）。

Table 1 同页还完整列出了继承自前版的 43 个 NetFlow 特征（五元组、L7 协议、进出字节/包数、流时长、三组 TCP 标志、TTL、最长/最短包、双向每秒字节、重传字节与包数、双向平均吞吐、五档包长计数、TCP 窗口、ICMP、DNS 三项、FTP 返回码等）。

## 关键数字（带页码 / 表号）

### 标签分布（Table 2，第 9 页）

| 数据集 | 恶意流 | 良性流 | 总流数 |
| --- | --- | --- | --- |
| NF3-UNSW-NB15 | 127,693（5.40%） | 2,237,731（94.60%） | 2,365,424 |
| NF3-CSE-CIC-IDS2018 | 2,600,903（12.93%） | 17,514,626（87.07%） | 20,115,529 |
| NF3-ToN-IoT | 10,728,046（38.98%） | 16,792,214（61.02%） | 27,520,260 |
| NF3-BoT-IoT | 16,881,819（99.7%） | 51,989（0.3%） | 16,933,808 |

注：Table 2 的 NF3-UNSW-NB15 总数 2,365,424 与 Table 3（第 9 页）该列的 Total 2,850,806 不一致，且 Table 3 中 NF3-BoT-IoT 的 Total 16,881,819 只是恶意流数（未含 51,989 条良性流）。**原件未解释这两处不一致**，引用时应注明。

### 逐类攻击流数（Table 3，第 9 页，摘录）

- NF3-UNSW-NB15：Exploits 42,748、Fuzzers 33,816、Generic 19,651、Reconnaissance 17,074、DoS 5,980、Shellcode 4,659、Analysis 2,381、Backdoor 1,226、Worms 158。
- NF3-CSE-CIC-IDS2018：DDoS 1,324,350、BrutForce 575,194、DoS 302,966、BoT 207,703、Infiltration 188,152、Web Attacks 2,538。
- NF3-ToN-IoT：DDoS 4,141,256、XSS 2,834,435、Password 1,594,777、Scanning 1,358,977、Injection 381,777、DoS 203,456、Backdoor 203,384、MITM 6,013、Ransomware 3,971。
- NF3-BoT-IoT：DoS 8,034,190、DDoS 7,150,882、Reconnaissance 1,695,132、Theft 1,615。

### 类别字段的唯一值计数（Table 5，第 16 页）

| 数据集 | 源 IP 数 | 目的 IP 数 | 源端口数 | 目的端口数 |
| --- | --- | --- | --- | --- |
| NF3-UNSW-NB15 | 40 | 40 | 64,620 | 64,631 |
| NF3-CSE-CIC-IDS2018 | 183,806 | 29,226 | 65,325 | 63,353 |
| NF3-ToN-IoT | 15,396 | 9,011 | 65,536 | 65,536 |
| NF3-BoT-IoT | 20 | 291 | 65,536 | 65,536 |

**这张表对本课题实体级实验有直接意义**：UNSW-NB15 全库只有 40 个源 IP、40 个目的 IP，BoT-IoT 只有 20 个源 IP。在这类数据集上做 IP 对（实体）级聚合，实体数是两位数量级，任何实体级指标都会被极少数实体主导。

### 攻击的按天分布（Table 4，第 14 页）

| 天 | NF3-UNSW-NB15 | NF3-CSE-CIC-IDS2018 | NF3-ToN-IoT | NF3-BoT-IoT |
| --- | --- | --- | --- | --- |
| 1 | All | BruteForce | Benign-Only | Reconnaissance |
| 2 | All | DoS | Benign-Only | Reconnaissance |
| 3 | Benign-Only | DoS | Benign-Only | Reconnaissance |
| 4 | — | DDoS | Scanning | DoS, DDoS |
| 5 | — | DDoS | DoS, Scanning | Theft |
| 6 | — | Web-Attack | DDoS, Injection, DoS | Theft |
| 7 | — | Web-Attack | DDoS, Password | — |
| 8 | — | Benign-Only | XSS, Password | — |
| 9 | — | Infiltration | Backdoor, Ransomware | — |
| 10 | — | Infiltration | MITM, Backdoor | — |
| 11 | — | BoT | — | — |

作者据此指出：**大多数攻击类别是在不同天分别执行的**，唯一例外是 UNSW-NB15，其全部攻击同时注入；作者建议研究者逐类分别分析（第 14 页 §5.3 末）。

### 其余定性观察（无数值，仅图）

- 流长分布（Figure 2，第 10 页）：四个数据集中良性流普遍集中在最短的流长档；Backdoor 与 Worms 表现为更长的流；DoS/DDoS 在 BoT-IoT 中跨全部流长档广泛分布（第 10–11 页 §5.1）。
- IAT 分布（Figure 3/4，第 11–12 页）：ToN-IoT 中 MITM 与 Backdoor 在特定 IAT 区间出现明显峰值，作者推测与周期性信令或数据外传有关（第 12 页 §5.2）。**该推测无定量支撑，属作者的解读。**
- 数值字段时间序列（Figure 6，第 15 页）：IN_BYTES 与 OUT_BYTES、IN_PKTS 与 OUT_PKTS 呈对称模式。
- 时频谱图（Figure 8，第 18 页）：只在 NF3-UNSW-NB15 上做，取每个攻击类别「最常见的模式」画谱图，作者称 DoS 与 Worms 有相似之处但仍彼此可分，Fuzzers 有独特时频签名。作者在摘要中已自陈"our initial investigations have not yet yielded definitive results"（第 2 页 §1）。
- nProbe 默认导出间隔不超过两分钟，这一配置影响流长分布的观察上界（第 10 页 §5.1）。

## 可引用的逐字原文

- 关于时频分析的自我限定："our initial investigations have not yet yielded definitive results"（第 2 页 §1）。
- 关于本文范围："This analysis is not aimed at classifying or predicting specific types of network attacks"（第 10 页 §5 开篇）。

## 与本课题的关系

第 1 点是论文原结论的引用范围界定，第 2–4 点是本课题推论。

1. **可直接引用的**：既有 NetFlow 标准特征集缺失时序特征，导致序列模型无法在其上工作（第 2 页 §1、第 5–6 页 §3）；四个基准的标签分布与规模（Table 2、Table 3）；实体（IP）基数极小（Table 5）；多数基准把不同攻击分散在不同天执行（Table 4）。**不可引用为**任何检测性能结论或「时序特征有用」的实证支撑——本文没有训练任何模型，不存在带时序特征与不带时序特征的对照实验。

2. **对本课题特征合同——一份可对照的字段清单，不是可照搬的方案**：
   - Table 1（第 6 页）是目前公开文献里最完整的一份「NetFlow 侧可用统计量」清单，可用作本课题 LSPR 物化器字段设计的对照表，尤其是双向 IAT 四统计量（min/max/avg/stddev）与五档包长计数。
   - 但边界要写清：本课题的历史表示是**流序列上的因果前缀均值**，而 NF3 的 IAT 统计是**单条流内部的包级聚合**，两者聚合层级不同。NF3 不提供跨流的时序结构，因此它无法回答本课题「序列建模是否优于逐流」的问题。

3. **对「(a) 简单聚合胜过复杂序列模型」——本文不构成证据，但提供了一条方法论警示**：
   - 本文只到「时序信息可视化」为止，没有做任何模型对比。作者在结论中把「优化 ML 模型以有效利用本文引入的时序特征」列为**未来工作**（第 19 页 §6）。
   - 可提取的警示是 Table 4：如果攻击按天分离，那么一个按时间顺序切分的训练/测试划分会让某些攻击类在训练集中完全不出现。这解释了为什么在这类基准上「时序模型」的收益极难干净地测量——收益与「哪些类被切进测试集」高度耦合。本课题 LSPR23→LSPR24 若存在类似的类别删失，跨年 AP 的下降就不能全部归因于表示能力，**这是一条应当在本课题数据卡中显式核查的假设**。

4. **对实体级评价——一条限制条件而非支持证据**：
   - Table 5 说明常用 NIDS 基准的实体基数可能只有几十（UNSW-NB15 的 40 个源 IP、BoT-IoT 的 20 个）。这意味着**本课题实体级 AP 0.5233–0.5475 这类结果无法在这些基准上复现或交叉验证**：实体太少，指标方差会被少数实体完全支配。
   - 因此在写作时应把实体级评价的适用前提说清：需要实体基数足够大且实体间行为异质（LSPR 演习网络与 CSE-CIC-IDS2018 的 183,806 个源 IP 属于这一类），而不是对所有 NIDS 数据集都适用。

## 可迁移的机制

1. **`nprobe --dont-reforge-time`**：从 PCAP 重建流记录时保留原始抓包时间戳的具体做法（第 8 页 §4.2），是任何跨年度时序实验的前置条件，值得写入本课题物化器的检查清单。
2. **精确时间戳 + 五元组双键打标**，而不是仅靠五元组或仅靠时间窗（第 8 页 §4.2）。
3. **「攻击按天分布表」（Table 4）这一数据卡形式**：把每个类别的活跃时间段显式列出，供切分设计时核查类别删失。本课题的 LSPR23/LSPR24 数据卡目前缺少等价的表。
4. **逐分钟聚合的唯一 IP / 唯一端口计数时间序列**（Figure 7，第 17 页）作为轻量级实体活跃度诊断，可用于判断实体级聚合窗口的合理尺度。

## 未在原件中定位到的项

- **任何检测性能指标**：全文无准确率、F1、AUC 等。
- **Table 2 与 Table 3 总数不一致的原因**（UNSW-NB15 的 2,365,424 vs 2,850,806；BoT-IoT 的 Total 未计入良性流）：原件未解释。
- **流长分布图的横轴单位**：Figure 2 的图内轴标为 "Flow Length (Seconds)"，而图题写作"the x-axis represents the length of flows in milliseconds"（第 10 页），二者矛盾，原件未订正。
- **谱图的构造细节**：窗长、重叠、采样率、"most repeated pattern" 的定义均未给出（第 17–18 页 §5.5）。
- **转换所用 nProbe 版本号**：只说明运行于 Ubuntu 20.04 LTS，未给版本（第 7 页 §4.2）。
- **原件封面无会议/期刊信息**，只有年份 2025 与 arXiv 标识。

## 文献信息

- arXiv：<https://arxiv.org/abs/2503.04404>（v2，2025-03-09）
- 数据发布：`https://staff.itee.uq.edu.au/marius/NIDS_datasets/`（参考文献 1，第 19 页；未在本地核验）
- 前置版本：Sarhan et al., "NetFlow datasets for machine learning-based NIDS"（Big Data Technologies and Applications 2021）与 "Towards a standard feature set for NIDS datasets"（Mobile Networks and Applications 2022）
- 本地 PDF：`raw/papers/datasets/analog-benchmarks/2025-Temporal-Analysis-NetFlow-Datasets-NIDS-arXiv2503.04404.pdf`（24 页）
- 本地 PDF SHA-256：`9fec642b43ad842130f47d1778c275f24037d2f12b551fb2f6db5ac0ec5847bd`
- 阅读方式：`pdftotext -layout` 全文 1,343 行；Table 1–5 均可完整提取并已逐页核对页码，八张图仅有图题与轴标散落文本。
