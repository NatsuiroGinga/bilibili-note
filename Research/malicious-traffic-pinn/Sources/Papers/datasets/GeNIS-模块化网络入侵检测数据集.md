---
title: "GeNIS：用于网络入侵检测与分类的模块化数据集"
authors:
  - Miguel Silva
  - Daniela Pinto
  - João Vitorino
  - José Gonçalves
  - Eva Maia
  - Isabel Praça
year: 2025
date: 2026-07-22
journal: "Data in Brief, 60, 111487"
source_pdf: "[[raw/papers/1-s2.0-S2352340925002197-main.pdf]]"
verified_full_pdf: "[[raw/papers/1-s2.0-S2352340925002197-main (2).pdf]]"
doi: "10.1016/j.dib.2025.111487"
tags:
  - 网络安全
  - 恶意流量检测
  - 数据集
  - GeNIS
  - 网络流
  - 类型/论文
aliases:
  - GeNIS 原始论文
  - Silva2025-GeNIS
key_finding: "GeNIS 提供按攻击步骤分离的 PCAPNG、5/10/30/60 秒流表和场景表，但官方随机分层留出协议会混合同源时序信息；其 125 字段原始流表远比当前 8 字段适配器丰富，足以支持方向、突发、时序和协议状态审计，却仍不直接观测链路容量与队列状态。"
method: "Airbus CyberRange 企业网络仿真、BUP 良性行为生成、八个顺序攻击场景、HERA 多时间间隔流聚合与分层标签"
related:
  - "[[恶意流量数据集引用核验]]"
  - "[[HIKARI-2021机器学习分类评估]]"
---

# GeNIS：用于网络入侵检测与分类的模块化数据集

> Miguel Silva 等，2025，`Data in Brief` 第 60 卷，文章号 111487，14 页。

## 一句话

GeNIS 的价值不只是样本较新，而是同时保留**攻击步骤、原始包、不同流间隔、场景组合、时间戳和 125 个 Argus/HERA 字段**；正式实验应从这些结构中构造会话或场景前向划分，而不能直接复用发布方的随机分层训练/留出文件。

## 来源与文件完整性核验

### 论文身份

- 完整题名：`GeNIS: A modular dataset for network intrusion detection and classification`。
- DOI：<https://doi.org/10.1016/j.dib.2025.111487>。
- 期刊：`Data in Brief`，第 60 卷，2025 年，文章号 111487。
- 作者与单位：Miguel Silva、Daniela Pinto、João Vitorino、José Gonçalves、Eva Maia、Isabel Praça；葡萄牙波尔图理工学院工程学院 GECAD 研究组（PDF 第 1 页）。
- 数据 DOI：<https://doi.org/10.5281/zenodo.14919237>（PDF 第 2 页“规格表”）。

### 两份本地 PDF 的关系

| 文件                                    | SHA-256                                                            |     文件大小 | 可读内容                  | 裁决                 |
| --------------------------------------- | ------------------------------------------------------------------ | -----------: | ------------------------- | -------------------- |
| `1-s2.0-S2352340925002197-main.pdf`     | `db5ee7b93ee9f9158354a036cdaf0c7c7d445a71ef97c0ccc75359b1abcfe1b2` | 556,276 字节 | 只能读出印刷页 1、8 至 14 | 页面树损坏的下载副本 |
| `1-s2.0-S2352340925002197-main (2).pdf` | `58d2180a12b7e89739d384c0b27a4f1af3904213e67a483c43edf64049f76ad5` | 555,672 字节 | 印刷页 1 至 14 完整       | 本次逐页核验基准     |

两份文件的题名、作者、期刊、年份、DOI、创建时间和 14 页元数据相同。第一份 PDF 的 8 个可读页面与第二份的第 1、8 至 14 页逐页文本哈希完全相同。因此它们不是两个论文版本，第一份只是缺少印刷页 2 至 7 的损坏副本。本笔记保留用户最初指定文件作为 `source_pdf`，所有页码事实均由完整的第二份复核。

## 研究目标与数据价值

论文针对中小企业网络入侵数据的三个缺口：现有数据常只有孤立攻击，流导出器和字段不兼容，且缺少按攻击步骤拆分的模块化原始捕获。GeNIS 因而同时提供原始包、流表、顺序场景和预处理表，使研究者可以重新选择流导出器、时间间隔和特征，而不必被固定特征集约束（PDF 第 1 至 3 页）。

论文报告的数据总量为（PDF 第 2 页、第 12 页表 12）：

- 37,681,001 个网络包；
- 2,737,930,223 字节；
- 5 秒间隔下 2,806,168 条流；
- 10 秒间隔下 1,504,184 条流；
- 30 秒间隔下 607,933 条流；
- 60 秒间隔下 368,556 条流。

## 采集环境与拓扑

### 仿真与监测环境

- 平台：Airbus CyberRange。
- 资源：32 GHz 处理器算力、112 GB 内存、4 TB 存储。
- 监测：交换端口分析器镜像多个接口，将流量发送到隔离监测机；`dumpcap` 顺序记录原始包。
- 采集日期：2025-02-06 至 2025-02-12。
- 日期角色：2 月 6 至 7 日采集工作日良性活动，2 月 8 日采集周末背景活动，2 月 10 至 12 日执行攻击（PDF 第 5 至 6 页）。

### 网络拓扑

论文文字称环境包含六个 LAN。图 1 实际画出以下网段和节点（PDF 第 6 至 7 页、图 1）：

| 网段            | 地址               | 主要节点或用途                             |
| --------------- | ------------------ | ------------------------------------------ |
| DMZ             | `192.168.128.0/24` | FTP、Postfix、域名服务器、代理、Web 服务器 |
| 路由互联段      | `192.168.129.0/24` | Router-1 与 Router-2 互联                  |
| Server LAN      | `192.168.130.0/24` | Active Directory、Mail、DFS                |
| Admin LAN       | `192.168.131.0/24` | Centreon、Admin-1、Admin-2                 |
| User LAN        | `192.168.132.0/24` | User-1、User-2、Kali-User、User-3          |
| Remote User LAN | `192.168.141.0/24` | Kali-WAN、User-4                           |
| WAN             | 图中单独绘制       | Router-1 与 Router-3 之间的外部网络        |

攻击者分别位于 User LAN 的 `Kali-User` 和 Remote User LAN 的 `Kali-WAN`。这里的地址和节点非常适合分组、复核场景与生成真实时间顺序，但**不应直接作为检测模型输入**，否则模型可能记住实验环境身份。

## 良性与攻击活动

### 良性活动

良性用户由 Benign User Profiler 生成两个配置（PDF 第 6 至 8 页、表 2 至 3）：

1. 普通用户配置运行在 User-1、User-3，模拟邮件、网页、更新等办公行为；两台机器采用相同脚本但错开 5 分钟。
2. 管理员配置运行在 Admin-2，模拟 FTP 上传、SSH 远程操作、DNS 检查、SMB 管理共享和 Web 服务测试。
3. 背景流量单独被动捕获，包含 ARP、Active Directory 相关 NBNS、TCP 和 DNS 等系统活动。

### 八个顺序攻击场景

每一步之间约暂停 5 分钟，先分析上一阶段再继续，形成可用于多阶段检测的顺序结构（PDF 第 8 至 12 页、表 4 至 11）。

| 场景 | 顺序                              | 最终攻击                |
| ---- | --------------------------------- | ----------------------- |
| 1    | DNS 发现 → NMAP → 攻击            | Hulk HTTP 洪泛          |
| 2    | DNS 发现 → NMAP → 攻击            | Slowloris               |
| 3    | DNS 发现 → NMAP → 攻击            | UDP 洪泛                |
| 4    | DNS 发现 → NMAP → 攻击            | ICMP 洪泛               |
| 5    | DNS 发现 → NMAP → 攻击            | Push/Ack 洪泛           |
| 6    | DNS 发现 → NMAP → 攻击            | SMB 凭据暴力破解        |
| 7    | DNS 发现 → NMAP → 攻击            | SSH 凭据暴力破解        |
| 8    | DNS 发现 → NMAP 侦察与映射 → 攻击 | SSH 与 FTP 凭据暴力破解 |

## 数据层级、文件组织与窗口语义

| 层级             | 内容                           | 关键文件或子目录                                              | 适合用途                           |
| ---------------- | ------------------------------ | ------------------------------------------------------------- | ---------------------------------- |
| `0-info`         | 字段字典和标签真值             | `genis-features.csv`、`genis-ground-truth.csv`                | 字段、单位、攻击时间和连接匹配审计 |
| `1-packets`      | 按子类分开的 PCAPNG            | 8 类攻击捕获、3 类良性捕获                                    | 统一重提取或协议层复核             |
| `2-flows`        | 按子类分开的完整流表           | `flows-5-sec`、`flows-10-sec`、`flows-30-sec`、`flows-60-sec` | 会话、时间和字段级实验             |
| `3-scenarios`    | 攻击步骤与对应时段良性流量组合 | 四种间隔下的 `scenario-1` 至 `scenario-8`                     | 场景留出、多阶段检测               |
| `4-preprocessed` | 特征筛选后的训练与留出文件     | 四种间隔各一组 `train`、`test`                                | 发布方快速基线，不适合严格时间泛化 |

HERA 的“流间隔”不是简单地把所有流切成互不重叠的固定窗口。只要流仍在活动，工具会按指定秒数输出新的流记录；间隔越短，更新越频繁（PDF 第 12 页，4.12 节）。因此，同一 `FlowID` 的连续行可能是同一活动流的阶段更新。构造四窗口历史时必须检查 `StartTime`、`LastTime`、`Rank`、`Trans` 和连续性，不能默认四行是独立控制体。

## 标签体系

论文表 1 定义三层标签（PDF 第 3 页）：

| `BinaryLabel` | `CategoryLabel` | `SubCategoryLabel`                                                |
| ------------: | --------------- | ----------------------------------------------------------------- |
|             0 | `benign`        | `benign-admin`、`benign-background`、`benign-user`                |
|             1 | `bruteforce`    | `bruteforce-ftp`、`bruteforce-smb`、`bruteforce-ssh`              |
|             1 | `dos`           | `dos-hulk`、`dos-icmp`、`dos-pushack`、`dos-slowloris`、`dos-udp` |
|             1 | `recon`         | `recon-dns`、`recon-nmap`                                         |

这三个字段都是**监督标签**，不得进入模型的观测输入。表 12 使用了 `benign-users`，而表 1 使用 `benign-user`；代码映射应以实际 CSV 值为准并保存别名归一化记录。

## 完整流程字段与单位

论文正文没有打印 125 个字段，只在第 4 页说明 `0-info/genis-features.csv` 保存“全部字段、类型和说明”。以下清单来自同一 Zenodo 记录的官方 `0-info.zip`，不是根据当前适配器反推。官方归档 MD5 为 `432ada3813f0261ac8b5e371ea4d729e`。

### 记录、时间与聚合字段，共 14 个

- `FlowID`：源/目的端口与协议组成的流标识，无物理单位。
- `Rank`、`Seq`：记录顺序号和 Argus 序号，无物理单位。
- `StartTime`、`LastTime`：记录起止时间戳；字典未规定序列化单位，真值文件表现为带小数的 Unix 时间。
- `Trans`：聚合记录数，单位为条。
- `Dur`、`RunTime`、`IdleTime`、`Mean`、`StdDev`、`Sum`、`Min`、`Max`：记录持续时间及其聚合统计；官方字典未声明时间单位。

### 标志、端点、协议和路由元数据，共 29 个

- `Flgs`：事务中观察到的流状态标志。
- `SrcMac`、`DstMac`、`SrcOui`、`DstOui`：源/目的 MAC 与厂商 OUI。
- `SrcAddr`、`DstAddr`：源/目的 IP 地址。
- `Proto`、`Sport`、`Dport`：协议、源端口、目的端口。
- `sTos`、`dTos`、`sDSb`、`dDSb`：双向服务类型与差分服务字段。
- `sCo`、`dCo`：源/目的 IP 国家代码。
- `sTtl`、`dTtl`、`sHops`、`dHops`：双向 TTL 与估计跳数。
- `sIpId`、`dIpId`：双向 IP 标识符。
- `sMpls`、`dMpls`：双向 MPLS 标识。
- `AutoId`：自动生成的数据库标识。
- `sAS`、`dAS`、`iAS`：源、目的和 ICMP 中间节点自治系统。
- `Cause`：Argus 记录原因，取值包括 `Start`、`Status`、`Stop`、`Close`、`Error`。

### 交互、包、字节和生产消费统计，共 13 个

- `NStrok`、`sNStrok`、`dNStrok`：总、源向目的、目的向源的观测按键次数，单位为次。
- `TotPkts`、`SrcPkts`、`DstPkts`：总、正向、反向包数，单位为包。
- `TotBytes`、`SrcBytes`、`DstBytes`：总、正向、反向事务字节，单位为字节。
- `TotAppByte`、`SAppBytes`、`DAppBytes`：总、正向、反向应用层字节，单位为字节。
- `PCRatio`：生产者/消费者比，无量纲。

### 负载、丢失、重传、缺口和速率，共 17 个

- `Load`、`SrcLoad`、`DstLoad`：总、正向、反向负载，单位为比特/秒。
- `Loss`、`SrcLoss`、`DstLoss`：重传或丢弃包数，单位为包；`pLoss` 为百分比。
- `Retrans`、`SrcRetra`、`DstRetra`：总、正向、反向重传包数；`pRetran` 为百分比。
- `SrcGap`、`DstGap`：数据流中缺失的双向字节数，单位为字节。
- `Rate`、`SrcRate`、`DstRate`：总、正向、反向包速率，单位为包/秒。官方字典将 `DstRate` 类型误写为 `Countinuous`，应按连续数值处理。
- `Dir`：事务方向，无物理单位。

### 包间到达时间与抖动，共 20 个

- 源向字段：`SIntPkt`、`SIntPktMin`、`SIntPktMax`、`SIntDist`、`SIntPktAct`、`SIntActDist`、`SIntPktIdl`、`SIntIdlDist`。
- 目的向字段：`DIntPkt`、`DIntPktMin`、`DIntPktMax`、`DIntDist`、`DIntPktAct`、`DIntActDist`、`DIntPktIdl`、`DIntIdlDist`。
- 抖动字段：`SrcJitter`、`SrcJitAct`、`DstJitter`、`DstJitAct`。

字典明确把包间到达时间和抖动标为毫秒；其中 `SIntDist`、`DIntDist` 和空闲分布字段的描述未对每个分布量重复声明单位，正式实现应延续 HERA 定义并做样本统计复核。

### 状态、缓存、TCP 窗口和 VLAN，共 15 个

- `State`：事务状态。
- `srcUdata`、`dstUdata`：源/目的用户数据缓冲，字典未声明单位。
- `SrcWin`、`DstWin`：源/目的 TCP 窗口通告值，字典未声明单位。
- `sVlan`、`dVlan`、`sVid`、`dVid`、`sVpri`、`dVpri`：双向 VLAN 标识与优先级。
- `SRange`、`ERange`：过滤时间范围起止时间戳。
- `SrcTCPBase`、`DstTCPBase`：双向 TCP 基准序列号。

### TCP 建连、ICMP、偏移和包长，共 12 个

- `TcpRtt`：TCP 建连往返时间，为 `SynAck + AckDat`；单位未在字典中声明。
- `SynAck`：SYN 到 SYN-ACK 的时间；单位未声明。
- `AckDat`：SYN-ACK 到 ACK 的时间；单位未声明。
- `TcpOpt`：发起连接时观察到的 TCP 选项。
- `Inode`：ICMP 中间节点。
- `Offset`：记录在文件或流中的字节偏移，单位为字节。
- `sMeanPktSz`、`dMeanPktSz`：双向平均包长。
- `sMaxPktSz`、`dMaxPktSz`：双向最大包长。
- `sMinPktSz`、`dMinPktSz`：双向最小包长。

包长字段的名称和描述表明其为包尺寸，但官方字典没有在单位列中明确写“字节”，正式论文应说明采用 HERA/Argus 的字节口径，而不是只凭字段名断言。

### 连接上下文和标签，共 5 个

- `Ssaddr`：同一服务与源地址的连接数。
- `Sdaddr`：同一服务与目的地址的连接数。
- `BinaryLabel`：0 为良性、1 为恶意。
- `CategoryLabel`：`benign` 或攻击大类。
- `SubCategoryLabel`：具体流量子类。

前述分组共计 125 个字段，其中最后三个是标签。地址、端口、时间和标识字段可以用于分组、排序、去重与泄漏审计，但不应直接输入主检测模型。

## 类别规模

论文表 12 给出不同流间隔下的类别规模（PDF 第 12 页）：

| 子类                |    5 秒 |   10 秒 |   30 秒 |  60 秒 |
| ------------------- | ------: | ------: | ------: | -----: |
| `dos-udp`           | 786,432 | 393,216 | 131,072 | 65,536 |
| `dos-icmp`          | 786,432 | 393,216 | 131,072 | 65,536 |
| `dos-pushack`       | 785,472 | 392,736 | 130,942 | 65,806 |
| `dos-slowloris`     | 255,311 | 168,116 |  85,212 | 51,729 |
| `dos-hulk`          |  93,938 |  67,821 |  51,327 | 47,033 |
| `recon-nmap`        |  27,713 |  27,713 |  27,713 | 27,713 |
| `benign-background` |  20,649 |  17,180 |  12,810 | 10,286 |
| `benign-user`       |  20,355 |  18,048 |  15,641 | 12,851 |
| `bruteforce-ssh`    |  12,388 |   8,677 |   4,696 |  4,688 |
| `bruteforce-smb`    |  10,002 |  10,001 |  10,001 | 10,001 |
| `benign-admin`      |   4,112 |   4,096 |   4,083 |  4,013 |
| `bruteforce-ftp`    |   3,344 |   3,344 |   3,344 |  3,344 |
| `recon-dns`         |      20 |      20 |      20 |     20 |

数据极端偏向洪泛攻击，尤其是 UDP、ICMP 和 Push/Ack。随机抽样很容易让模型主要学习高流量洪泛模式；宏平均 F1、每类召回、未知类留出和自然比例误报率必须同时报告。

## 官方划分与防泄漏风险

### 论文原文事实

发布方的 `4-preprocessed` 目录按每个流间隔提供一个训练文件和一个留出文件，并说明使用打乱和分层保持类别比例（PDF 第 5 页）。论文没有定义验证集，也没有提出时间、会话、攻击步骤或捕获文件级划分。

### 本课题推断

以下是根据论文数据结构得到的实验风险，不是论文作者的原话：

1. 良性和攻击在不同日期采集，绝对时间、源文件、地址和端点可能直接编码标签。
2. 5、10、30、60 秒文件来自相同 PCAPNG，同源版本不得跨训练、验证和测试。
3. 同一长流会按间隔反复输出，行级随机划分可能把相邻或累积状态分到两侧。
4. 每个 DoS 子类只有很少的完整运行，行数巨大不等于独立场景多。
5. `3-scenarios` 比随机预处理文件更适合做攻击链留出，但仍要确保同一原始捕获不跨分区。

因此，本课题应继续采用会话、时间和场景约束的前向协议，不使用发布方随机训练/留出文件作为正式泛化证据。

## 论文明确限制

作者在 PDF 第 13 页指出：攻击只作用于特定机器，协议和 LAN 覆盖仍需扩大；良性活动也不能覆盖复杂网络中用户、应用和设备的全部变化。除此之外，本课题还应注意：CyberRange 仿真不提供公开网络中的真实队列、容量和拥塞真值，不能把流统计直接解释为已观测物理状态。

## 对当前 8 字段适配器的直接影响

当前 `genis.py` 读取 12 个数值字段和 3 个标签字段，最终只形成 8 个模型输入：

| 当前输入             | GeNIS 来源                      | 保留信息         |
| -------------------- | ------------------------------- | ---------------- |
| `total_packets`      | `TotPkts`                       | 总包数           |
| `total_bytes`        | `TotBytes`                      | 总事务字节       |
| `packet_length_mean` | `TotBytes / TotPkts`            | 平均事务字节/包  |
| `packet_length_min`  | `min(sMinPktSz,dMinPktSz)`      | 双向最小包长     |
| `packet_length_max`  | `max(sMaxPktSz,dMaxPktSz)`      | 双向最大包长     |
| `iat_mean_ms`        | `SIntPkt`、`DIntPkt` 按包数加权 | 双向平均到达间隔 |
| `packet_rate`        | `Rate`                          | 总包速率         |
| `byte_rate`          | `Load / 8`                      | 总字节速率       |

该接口舍弃了：

- `StartTime`、`LastTime`、`FlowID`、`Rank`、`Trans` 等历史构造信息；
- `SrcPkts/DstPkts`、`SrcBytes/DstBytes`、`SrcRate/DstRate` 等方向性；
- 到达间隔最小值、最大值、活动/空闲分布和四个抖动字段；
- `Loss`、`Retrans`、`Gap` 等丢失与重传信息；
- TCP 标志、事务状态、握手时延、窗口和选项；
- 协议、端口、服务连接数等连接上下文；
- 应用层字节与事务总字节之间的协议层差异。

这些字段不能全部无条件输入模型，其中地址、端口和绝对时间具有泄漏风险；但方向、波动、活动/空闲、TCP 状态和丢失特征应进入任务十七的**输入充分性消融候选**，而不是在数据适配阶段全部永久删除。

## 与任务十七五字段接口的关系

任务十七当前提出的五字段为 `total_packets`、`total_bytes`、`packet_length_mean`、`packet_rate`、`byte_rate`。GeNIS 能构造这五个量，但这不等于它们与 HIKARI、ns-3 的物理语义已经一致：

- GeNIS 的 `TotBytes` 是双向事务字节；
- HIKARI 当前适配器使用双向负载字节；
- ns-3 记录的是瓶颈队列规则层的 L3 字节；
- GeNIS/HIKARI 是流记录，ns-3 是 0.1 秒瓶颈窗口。

因此，五字段只是**待统一口径的工程候选接口**。当前严格语义交集仍为空，任务十七必须先统一聚合对象和协议层字节口径。若继续只用五字段，还会进一步删除最小/最大包长与平均到达间隔，不能预先宣称足以辨识容量或队列状态。

## 对第三章实验的直接结论

1. GeNIS 数据本身并非只有 8 个字段；前期实验使用的是过度压缩的适配视图。
2. 已有 8 字段结果可以证明该视图上的已见攻击可分类性，但不能证明原始数据无更多有效信息。
3. B0/B1 失败只裁决“当前压缩输入下的直接状态注入”，不能否定扩展观测后的物理表征。
4. 四窗口必须从原始 `FlowID`、`StartTime`、`LastTime` 和发布文件重建，不能从已打乱的多任务 JSONL 拼接。
5. 物理状态监督仍只能来自 ns-3；GeNIS 的时间与流字段只提供公开观测和域覆盖证据，不提供真实队列标签。
6. 在进入物理软令牌训练前，必须比较五字段、当前八字段和扩展无身份泄漏字段，并与常数状态下界比较。

## 原始摘要要点

作者将 GeNIS 定位为面向中小企业网络攻击的模块化数据集：在 CyberRange 上记录顺序攻击、普通用户、管理员与背景活动，提供超过 3,700 万个原始包和四种时间间隔的 280 万余条流，以支持不同流导出器、特征提取器和检测模型。该段为摘要中文转述，原文见 PDF 第 1 至 2 页。

## 文献信息

- 论文 DOI：<https://doi.org/10.1016/j.dib.2025.111487>
- 官方数据：<https://doi.org/10.5281/zenodo.14919237>
- 建议引用：SILVA M, PINTO D, VITORINO J, et al. GeNIS: A modular dataset for network intrusion detection and classification[J]. Data in Brief, 2025, 60: 111487.
