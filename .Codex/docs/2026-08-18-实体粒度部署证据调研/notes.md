# 实体粒度判定单元证据 — 过程笔记（逐篇落盘）

建立：2026-08-18。每完成一篇全文或一组查询立即追加，不事后补写。

---

## 检查点 0（任务起点）

- 已完成：建 `task_plan.md`、本文件。
- 下一步：建本地 427 篇 PDF 的纯文本缓存（scratchpad），跑第一组关键词。
- 未关闭疑点：无。
- 阻塞：无。

---

## 查询与命中记录

（按时间顺序追加）

## 检查点 1 — 本地全库文本缓存与首轮关键词扫描（2026-08-18）

- 已完成：`raw/papers/` 下 427 篇 PDF 用 `pdftotext` 提取到 scratchpad 缓存
  `/private/tmp/claude-501/-Users-bilibili-personal-note/a6b7721f-65a8-411a-9630-071c1601ca01/scratchpad/pdftext/`，
  成功 417 篇，失败 10 篇（列在下方「提取失败清单」）。
- 首轮 `rg` 扫描已跑三组关键词，命中清单见下。
- 下一步：按优先级逐篇全文核验，先 Gehri 2023 → Yen 2013 Beehive → Bilge 2012 DISCLOSURE
  → Kanzig 2019 → Hu 2016 BAYWATCH → Zhang 2023 → Lee & Stolfo 2000 → Pevny 2016 →
  2026 Contextualized-NetFlow 综述 → Dijk LSPR 系列 → 反面证据（Zhao 2025 Sweet Danger 等）。
- 阻塞：无。

### 提取失败清单（pdftotext 失败，非「不存在」）

`datasets/quic/citing/2022-Chaudhary-YouTube-QUIC-vs-Middleboxes.pdf`、
`datasets/quic/citing/2023-Caiazza-Energy-Consumption-HTTP-Versions-PMC.pdf`、
`datasets/quic/citing/2024-Muecke-ReACKed-QUICer-Instant-ACK-QUIC-Handshakes-IMC.pdf`、
`grpo/2511.03527.pdf`、`grpo/2512.15347.pdf`、`grpo/2601.22478.pdf`、
`methodology/2007-van-der-Laan-Super-Learner.pdf`、`methodology/2010-Polley-Super-Learner-Dissertation.pdf`、
`methodology/2019-Azizzadenesheli-RLLS.pdf`、`methodology/2020-Garg-Unified-Label-Shift.pdf`。
以上均与本论断无关（QUIC 中间盒、GRPO、Super Learner、标签漂移），不影响本轮结论。

### 查询组 Q1：告警疲劳 / SOC 分析员处置能力

查询式：`rg -i -e 'alert fatigue' -e 'alerts per day' -e 'alert volume' -e 'SOC analyst' -e 'security operations cent'`
命中 11 篇：Luxemburk 2022（reject option）、Pevny 2016（MIL 树结构）、
2026 博弈论 MDP 隐蔽入侵、Meier 2025 LSPR24 蓝队自动化、Yen 2013 Beehive、
ARES 2025 会议录第二卷、Leoste 2025 LSPR23/24 对比、Zhang 2023 聚合信标检测 ACSAC、
StealthCup 2025 规避 CTF、`datasets/1-s2.0-S2214212624001492-main.pdf`、Sun 2024 在线自适应阈值。

### 查询组 Q2：host-level / entity-level / per-host 判定单元

查询式：`rg -i -e 'host-level' -e 'host level' -e 'per-host' -e 'entity-level' -e 'per-entity' -e 'asset-level'`
命中 6 篇（含计数）：2026 Contextualized-NetFlow NIDS 综述(4)、同篇 arXiv 版(4)、
`datasets/LSPR24/ssrn-6597680.pdf`(4)、Lee & Stolfo 2000 TISSEC(3)、
ARES 2025 会议录(1)、Cui 2023 CBSeq(1)。

### 查询组 Q3：infected host / compromised host

命中 16 篇，计数最高：Gehri 2023 CyCon(18)、Bilge 2012 DISCLOSURE(8)、
Kanzig 2019 CyCon(7)、Hu 2016 BAYWATCH(6)、Yen 2013 Beehive(5)、
Zhang 2023 ACSAC(4)、Cui 2023 CBSeq(4)、Anderson 2016(1)、Gupta 2025 ARES(1)。

---

## 篇目 1 — Gehri et al. 2023, CyCon（本章已引 [3]，本轮复核）

- 题录：Lina Gehri, Roland Meier, Daniel Hulliger, Vincent Lenders.
  "Towards Generalizing Machine Learning Models to Detect Command and Control Attack Traffic."
  *2023 15th International Conference on Cyber Conflict: Meeting Reality (CyCon)*,
  NATO CCDCOE Publications, Tallinn, 2023.（会议录扉页第 1 页已核）
- 原件：`raw/papers/datasets/locked-shields-related/2023-Gehri-Towards-Generalizing-ML-C2-Detection-CyCon.pdf`
- 证据等级：**全文核验**
- 关键位置：摘要（PDF p.1）；§6.1 Flow-Based Models 结果（提取文本 L861）；
  §6.2 Host-Based Models（提取文本 L955–998，对应正文标注页 "13"–"14"）；§7 Conclusion。
- 核验要点（中文转述）：
  1. 判定单元定义在 §6.2：把「受感染主机」定义为至少作为一条被标注恶意流源 IP 的 IP 地址，
     把「检出的受感染主机」定义为参与至少 n∈{1,5,10,100} 条被预测为恶意的流的 IP 地址。
     即先做逐流分类，再按源 IP 计数阈值升格为主机级判定。
  2. 逐流跨网退化：迁移到 Country B 数据集时，逐流模型 F1 全部低于 0.2
     （原文 "the scores for Country B's dataset are all below 0.2"，L861）。
  3. 主机级挽回：同一模型在 Country B 检出 39 台受感染主机中的约 33 台，
     3,185 台正常主机中误报 119 台（L985–988）。
  4. Country A 各年份 n=1 时 FPR 均低于 4%；n>100 时检出率超过 90% 且 FPR 低于 4%（§7）。
  5. 部署动机（摘要，PDF p.1）：事件响应队伍常常要在**陌生网络**里找入侵，
     学到的模型往往无法泛化到不同网络条件。
- 与本论断关系：**直接支撑「聚合挽回表示层退化」（证据类四）与「实体级是可处置单元」（类一）**。
  是本章 3.2.3 已引 [3] 的原始出处，本轮复核数字与本章表述一致。
- 纳入理由：全文核验，数字与判定单元定义均可回溯。
- Zotero 状态：待补（本轮未写入 Zotero）。
- 待办：无。

---

## 篇目 2 — Yen et al. 2013, ACSAC（Beehive）

- 题录：Ting-Fang Yen, Alina Oprea, Kaan Onarlioglu, Todd Leetham, William Robertson,
  Ari Juels, Engin Kirda. "Beehive: Large-Scale Log Analysis for Detecting Suspicious Activity
  in Enterprise Networks." *ACSAC '13*, Dec. 9–13, 2013, New Orleans, LA, USA.
  ACM 978-1-4503-2015-3/13/12.（版权栏已核，PDF p.1）
- 原件：`raw/papers/methodology/multiple-instance/2013-Yen-Beehive-Enterprise-Log-Analysis-ACSAC.pdf`（10 页）
- 证据等级：**全文核验**
- 关键位置：§1 Introduction（PDF p.2，三层结构与「for each host per day」）；
  §2.3 Challenges（PDF p.3）；§3.2 Feature Extraction（每主机每日 15 维特征向量）；
  §3.3/§4 聚类与评估（PDF p.6–7）。
- 核验要点（中文转述）：
  1. **判定单元明确为「主机-日」**：系统为企业内每台专属主机每天生成一个含 15 个特征的向量，
     再对特征向量聚类，把离群主机报为「事件（incident）」交安全分析员。
  2. **规模与压缩比**：SIEM 每天平均收到 14 亿条日志（§2.3，PDF p.3）；
     工作日活跃主机 27,000–35,000 台（PDF p.6）；两周内共生成 784 个事件，
     平均每天 56 个、标准差 6.88（§4，PDF p.7）。即从 10^9 量级日志压到每天数十个实体级待办。
  3. **实体归并本身是工程难点**：论文把「多数网络设备只记录 IP 端点、
     需要跨日志关联才能把 IP 绑定到具体主机（尤其动态分配时）」列为三大挑战之一（§2.3）。
  4. **可处置性**：论文自述目标是产出 "accurate, actionable information"（§1 贡献列表，PDF p.2），
     事件随附所属簇的上下文（簇内主机数、簇平均特征向量），便于分析员快速定位区分性特征（§4.1）。
  5. 两周 784 个事件中只有 8 个与企业现有安全工具告警重叠（§4，PDF p.7）。
- 与本论断关系：**证据类一（实体级判定单元）＋ 类二（告警量与分析员处置能力）**的核心引文。
  可支撑「实体级判定把 10^9 量级观测压缩到人可逐条处置的每日数十条」。
- 纳入理由：全文核验，判定单元与告警量数字均在原文。
- Zotero 状态：待补。
- 待办：确认 ACSAC'13 正式页码（本 PDF 无印刷页码，为 ACM 版式无页眉页码），
  正式引用时补 pp. 199–208（**待核，尚未核实，不得直接写入正文**）。

---

## 篇目 3 — Bilge et al. 2012, ACSAC（DISCLOSURE）

- 题录：Leyla Bilge, Davide Balzarotti, William Robertson, Engin Kirda, Christopher Kruegel.
  "DISCLOSURE: Detecting Botnet Command and Control Servers Through Large-Scale NetFlow Analysis."
  *ACSAC '12*.（题名与作者已核，PDF p.1）
- 原件：`raw/papers/methodology/multiple-instance/2012-Bilge-DISCLOSURE-Botnet-C2-NetFlow-ACSAC.pdf`（10 页）
- 证据等级：**全文核验**
- 关键位置：§2 系统结构（提取文本 L203–208）；§3.1 NetFlow Attributes（PDF p.2，服务器 2-tuple 定义）；
  §3.2 特征按服务器分组（L302–312）；§6 评估 Table 3 / Table 4（PDF p.6）。
- 核验要点（中文转述）：
  1. **判定单元是实体而非流**：系统把每个服务器表示为「IP 地址 + 端口」二元组
     （原文 "a 2-tuple of IP address and port"，§3.1，PDF p.2），
     所有特征都通过「把流按其来源或目的服务器分组」后在实体上统计得到。
     论文明说其目标 "is not to identify bot-infected machines but to detect C&C servers"，
     检测阶段第一步就是**丢弃无法归属到某个服务器的 NetFlow**。
  2. **逐流信息不足的直接陈述**（§1）：NetFlow 记录没有载荷、是半双工单向的、
     且常按 1/10,000 采样；检测器必须在这三重损失下「识别微弱信号」。
     即单条流的信息量不足以支撑判定，必须在实体上聚合。
  3. **告警预算由人工核验能力反推**（§6）：原文写「信誉分数的计算方式可以按
     期望结果和安全管理员能承受的**每日告警数**来调；过滤越激进，被标为 C&C 的 IP 集合越小。
     实验中我们不断加强误报削减，**直到把告警量降到可以人工核验的水平**」。
  4. **实体级告警量的实测数字**：N1 网络经 MinFlows=50 过滤后剩 53,426 个服务器实体，
     在 1.0% / 0.5% / 0.3% / 0.0% FP 四个工作点分别标出 12,383 / 7,856 / 6,295 / 132 个服务器（Table 3）；
     叠加信誉过滤后降到 1,779 / 1,448 / 1,236 / 20 个（Table 4）。
     N2 网络对应为 4,937 / 3,166 / 1,958 / 960（Table 3）与 1,516 / 688 / 271 / 91（Table 4）。
  5. 最保守配置（0% FP + 信誉过滤）下运行一周，在 ISP 网络报出 91 个、
     在校园网报出 20 个此前未知的 C&C 服务器，111 条中 36 条（32.4%）经外部来源确认。
- 与本论断关系：**证据类一 + 类二 + 类三**。可支撑「实际部署把判定单元定在实体上，
  并按分析员可人工核验的告警数反推工作点」这一句。
- 纳入理由：全文核验，判定单元定义、逐流信息不足的理由、告警预算数字齐备。
- Zotero 状态：待补。
- 待办：补 ACSAC'12 正式页码（**待核**）。

### 检查点 2

- 已完成：篇目 1–3 全文核验并落盘。
- 下一步：Kanzig 2019 CyCon → Hu 2016 BAYWATCH → Zhang 2023 ACSAC 聚合信标 →
  Lee & Stolfo 2000 → Pevny 2016 MIL → 2026 Contextualized-NetFlow 综述。
- 未关闭疑点：ACSAC 两篇正式页码待核。
- 阻塞：无。

---

## 篇目 4 — Känzig et al. 2019, CyCon

- 题录：Nicolas Känzig, Roland Meier, Luca Gambazzi, Vincent Lenders, Laurent Vanbever.
  "Machine Learning-based Detection of C&C Channels with a Focus on the Locked Shields
  Cyber Defense Exercise." *2019 11th International Conference on Cyber Conflict: Silent Battle*,
  NATO CCD COE Publications, Tallinn, 2019.（扉页已核）
- 原件：`raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon.pdf`
- 证据等级：**全文核验**
- 关键位置：§1 Introduction / Problem statement（印刷 p.2–3）；§4 结果（印刷 p.13）；
  §5.A Identifying C&C Servers（印刷 p.16）。
- 核验要点（中文转述）：
  1. **问题陈述本身写在实体上**：「我们的目标是设计一个能识别 C&C 流量**和受感染主机**的系统」（§1）。
  2. **分类器是逐流的，但可交付物是实体**：§5.A 说能检测单条 C&C 流「显然可以用来识别
     C&C 服务器（这些流的目的端）和受感染主机（这些流的源端）」；
     在 Locked Shields 2018 开局只跑 30 分钟（11:00–12:00），
     就识别出 Cobalt Strike 报告中 12 台 C&C 服务器里的 10 台，
     并观察到蓝队网络中 5 个不同源 IP 在与这些服务器通信。
  3. **误报的运维含义**（§4，印刷 p.13）：「高精确率在本任务中尤其重要，
     因为大量误报会在行动中误导防守方」。逐流模型的 tuned 配置精确率 0.99。
- 与本论断关系：**证据类一的「运维处置需要」子项**，且是一个「逐流分类器 + 实体级交付」
  的两段式范例：报告出去的是 10 台服务器与 5 台主机，不是若干万条流。
- 注意（不得夸大）：本文逐流精确率很高（0.99），**不能用它论证「逐流一定失败」**；
  它论证的是「即使逐流指标好，最终交付单元仍是实体」。
- 纳入理由：全文核验；实体交付与运维理由均在原文。
- Zotero 状态：待补。

---

## 篇目 5 — Hu et al. 2016, DSN（BAYWATCH）

- 题录：Xin Hu, Jiyong Jang, Marc Ph. Stoecklin, Ting Wang, Douglas L. Schales,
  Dhilung Kirat, Josyula R. Rao. "BAYWATCH: Robust Beaconing Detection to Identify
  Infected Hosts in Large-Scale Enterprise Networks."
  *2016 46th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)*,
  pp. 479–490.（首页页眉与印刷页码已核：PDF p.1 = 印刷 p.479，PDF p.12 = 印刷 p.490）
- 原件：`raw/papers/attack-detection/encrypted/2016-Hu-BAYWATCH-Beaconing-Detection-DSN.pdf`（12 页）
- 证据等级：**全文核验**
- 关键位置：摘要与 §I Challenge 1（印刷 p.479–480）；§II 通信对定义（印刷 p.480）；
  §VI Investigation and Verification；§VIII 评估（印刷 p.488）。
- 核验要点（中文转述）：
  1. **判定单元是「通信对」（主机对）**：§II 明确「通信对定义为一对源端点与目的端点」，
     所有网络事件先按通信对配置分组，再进入 8 级过滤。
  2. **逐条事件不足以判定**（Challenge 1，印刷 p.480）：原文写
     "Beaconing is not an isolated event, but a sequence of temporally related events"，
     必须在上下文中成组分析；因此检测信标是一个大数据问题。
  3. **实体规模**：一个跨数十站点的大型企业网仅 HTTP(S) 协议就平均每天出现
     **5,300 万个不同通信对**（印刷 p.480）。
  4. **告警量落到人能处理的量级**：在 13 万台终端、5 个月、300 亿条事件的真实企业代理日志上，
     系统平均**每天报出约 26 个可疑信标案例**，其中排名靠前的超过 96% 被确认确属恶意
     （摘要与 §VIII）。前 50 个被确认为恶意的目的中 48 个（96%）找到公开恶意证据。
  5. **实体标识本身需要工程处理**：论文把源 IP 与 DHCP 日志中的 MAC 关联，
     理由是「相比 IP，MAC 在设备识别上更可靠，因为设备从不同网络接入时 IP 会变」（印刷 p.488）。
     全期观测到 24 万个 IP 但只有 13 万个不同 MAC。
  6. 5 个月内共 2,352 个不同目的被标为可疑；论文明说「人工逐个检查这些案例代价极高」，
     因而改用「小样本人工标注 + 分类器外推 + 按不确定度排序人工复核」的三段式。
- 与本论断关系：**证据类一（主机对判定单元）＋ 类二（告警量 26/天 vs 5,300 万通信对/天）
  ＋ 类三（信标不是孤立事件）**。是本轮最强的单篇证据之一。
- 纳入理由：全文核验，三类证据齐备且有硬数字。
- Zotero 状态：待补。

---

## 篇目 6 — Zhang et al. 2023, ACSAC

- 题录：Yizhe Zhang, Hongying Dong, Alastair Nottingham, Molly Buchanan, Donald E. Brown,
  Yixin Sun. "Global Analysis with Aggregation-based Beaconing Detection across Large
  Campus Networks." *ACSAC 2023*.（作者与题名已核，PDF p.1；印刷页码见提取文本 L457 附近的 "567"）
- 原件：`raw/papers/attack-detection/encrypted/2023-Zhang-Aggregation-Beaconing-Detection-ACSAC.pdf`
- 证据等级：**全文核验**
- 关键位置：§2 Motivation and Challenges；§3.2 系统概览；§4.1 算法；§6 Evaluation。
- 核验要点（中文转述）：
  1. **显式对比两种粒度**：§2 把既有工作归为「细粒度检测器」——按每个
     {源, 目的} 对重建时间序列，端点可用 {IP, 端口, MAC, User-Agent, 设备 ID} 与
     {IP, 端口, 完整域名, 顶级域, AS 号, URL} 表示；本文改为**按服务器（FQDN）聚合**
     所有设备的流量。
  2. **单个细粒度序列信息不足的实测**（§2 与图 1）：原文写
     "using any individual time series alone is insufficient for periodicity detection"，
     但把指向同一恶意域名的四个 {源, 目的} 对的信号按共享 FQDN 相加后，周期性模式就显现出来。
     跨协议、跨机构聚合还能揭示单一协议或单一网络中看不出的周期。
  3. **实体聚合是为了绕开主机跟踪失败**（§2 与 §4.1）：校园 SOC 往往**没有**完整的内部设备跟踪
     能力，NAT 部署复杂、部分子网无探针、日志基础设施过载时会丢记录，因此日志常缺 MAC；
     细粒度检测器还容易被 DNS fast-flux 与云端 C2 一域多 IP 规避。
     论文明说「基于服务器的聚合克服了 §2 描述的主机跟踪难题」。
  4. **告警预算与分析员**（§6）：原文写「鉴于真实 SOC 运营的资源约束，首要目标是
     压低误报并**把待人工核验的案例数维持在合理水平**；换言之，为 SOC 分析员**优先排序
     真正的恶意活动比压低漏报更重要**」，并注明该偏好已被两项访谈安全分析员的研究证实
     （其参考文献 [3] Alahmadi et al., USENIX Security 22；[39] SANS 2019 SOC Survey）。
  5. **实测告警量**：10 个月（2020-06-01 至 2021-03-31）两所大学校园网共 **752.3 亿条连接**；
     全局流水线**平均每天检出 77 个可疑信标案例**，最终**平均每天只有 10 个案例送交分析员
     人工核验**，日均误报 3–5 个，准确率 93.49%，比单校园本地流水线每天多检出 65.32% 的恶意域名。
  6. **实体聚合的代价（反面）**：§2 明确列出聚合的第一个挑战是
     「相比细粒度时间序列，**聚合信号中的噪声更大**」，因此必须额外引入 EMD 去噪。
- 与本论断关系：**证据类一 + 二 + 三 + 五**。第 6 条是本轮找到的第一条明确的「实体级聚合代价」。
- 纳入理由：全文核验，四类证据齐备。
- Zotero 状态：待补。
- 衍生待办（本地缺失，需联网补）：
  - Alahmadi, Axon, Martinovic. "99% False Positives: A Qualitative Study of SOC Analysts'
    Perspectives on Security Alarms." *USENIX Security 22*, pp. 2783–2800.（类二核心，本地无）
  - SANS Institute. *Common and Best Practices for SOCs: Results of the 2019 SOC Survey*.（类二，本地无）

---

## 篇目 7 — Lee & Stolfo 2000, ACM TISSEC

- 题录：Wenke Lee, Salvatore J. Stolfo. "A Framework for Constructing Features and Models
  for Intrusion Detection Systems." *ACM Transactions on Information and System Security*,
  Vol. 3, No. 4, November 2000, pp. 227–261.（版权页已核）
- 原件：`raw/papers/methodology/multiple-instance/2000-Lee-Stolfo-Framework-Constructing-Features-Models-IDS-TISSEC.pdf`
- 证据等级：**全文核验**
- 关键位置：§1（印刷 p.229–230）；§2.2（印刷 p.234）；§5.1.4 与表 VIII（印刷 p.242–243）。
- 核验要点（中文转述）：
  1. **判定单元仍是连接记录，但必须补实体范围的统计量**。论文明说：因为网络事件有时间性，
     尤其是探测类与拒绝服务类攻击，**加入 per-host 与 per-service 时间统计量能显著提升
     分类模型准确率**（印刷 p.234）。
  2. **具体特征**（表 VIII，印刷 p.243）：「同主机」特征只看过去 2 秒内与当前连接
     目的主机相同的连接——这类连接的计数、同服务比例、异服务比例、SYN 错误比例、REJ 错误比例；
     「同服务」特征对称定义。
  3. **慢速探测迫使换用实体窗口**（印刷 p.243）：有些慢速 PROBING 攻击的扫描间隔远大于 2 秒
     （每分钟甚至每几小时一次），在 2 秒窗口下产生不了「仅入侵」模式；
     作者于是**把连接记录按目的主机排序**，把时间窗换成 **100 条连接的「连接窗口」**，
     构造出一组镜像的「基于主机的流量特征」。
  4. **单条连接确实不足**（印刷 p.243）：R2L 与 U2R 攻击「嵌在数据包的数据部分，
     通常只涉及单个连接」，因而没有独特的频繁流量模式，自动特征构造对它们失效——
     反过来说明流量层面的判定必须依赖跨连接的实体上下文。
- 与本论断关系：**证据类三**（单条流信息不足，须补同主机聚合统计）。
  这是 KDD'99 `dst_host_*` 系列特征的来源。
- **重要边界（不得夸大）**：本文的判定单元**仍是连接记录**，不是主机。
  它只能支撑「实体上下文是必要输入」，**不能**支撑「实体是判定单元」。
- 纳入理由：全文核验，是「同主机计数特征」的原始文献。
- Zotero 状态：待补。

---

## 篇目 8 — El Mahdaouy et al. 2026, arXiv 预印本（上下文化 NetFlow NIDS 综述）

- 题录：Abdelkader El Mahdaouy, Issam Ait Yahia, Soufiane Oualil, Ismail Berrada.
  "Deep Learning for Contextualized NetFlow-based Network Intrusion Detection:
  Methods, Data, Evaluation and Deployment." arXiv:2602.05594v3 [cs.CR], 2026-03-03/04.
- 原件（库内两份同文）：
  `raw/papers/methodology/multiple-instance/2026-Contextualized-NetFlow-DL-NIDS-Survey.pdf`
  `raw/papers/datasets/analog-benchmarks/2026-Contextualized-NetFlow-NIDS-Survey-arXiv2602.05594.pdf`
- 证据等级：**全文核验**，但**是未经同行评议的 arXiv 预印本**，只能作为综述性框架引用，
  不能当作实测结论来源。
- 关键位置：摘要；§1 Introduction；§2 四维分类法；§5.3 Cross-Cutting Challenges；§7.1。
- 核验要点（中文转述）：
  1. **问题陈述与本章一致**：摘要写「许多现有的学习型检测器仍把入侵检测建成逐流分类，
     隐含地把每条流记录当作独立样本。**在真实攻击战役中这一假设通常不成立**，
     证据分布在**多条流与多台主机**上，跨分钟到数天，经由分阶段执行、信标、横向移动和数据外传展开。」
  2. **两条独立的失败机制**（§1）：
     (a) 表示层面——逐流模型忽略序列与关系依赖，把每条流当 IID 实例会丢掉多阶段隐蔽攻击的结构；
     (b) 运营层面——「**高逐流准确率在运营环境中并不够**：由于类别不平衡与基率谬误，
     即使误报率很低的检测器也会用告警淹没分析员」，此处援引 Axelsson 2000。
  3. **四维上下文分类法**：时间上下文、图/关系上下文、多模态上下文、多分辨率上下文；
     其中多分辨率维度「在包、流、会话到**主机**等不同粒度上聚合活动」。
  4. **实体状态是部署工程约束**（§7.1）：流式部署要「对**每主机聚合量**做带 TTL 的有状态缓存，
     以保证陈旧信息自动过期」，图系统还需动态邻域管理与剪枝来限界图规模。
  5. **反面提示**（§5.3 Cost and privacy）：多模态与多分辨率模型在高速链路上运行代价高；
     激进采样、压缩或选择性日志虽提升吞吐，但**有可能删掉这些模型本来要捕获的证据**。
- 与本论断关系：**证据类三的框架性引文 + 类二的机理（基率谬误）+ 类五的部分代价**。
- **重要边界**：预印本。可用于交代研究现状与问题框架，**不得**据其数字下实验结论。
- Zotero 状态：待补。
- 衍生待办：Axelsson 2000（基率谬误原文，本地无）；Sommer & Paxson 2010（本地无）。

---

## 篇目 9 — Pevný & Somol 2016/2017（树结构多示例学习，Cisco CTA）

- 题录：Tomáš Pevný, Petr Somol. "Discriminative models for multi-instance problems with
  tree-structure." arXiv:1703.02868v1 [cs.CR], 2017-03-07。
  （文件名标注 AISec；PDF 内版权行为 "Copyright 20XX ACM X-XXXXX-XX-X/XX/XX" 的**未填模板**，
  **正式会议与页码待核**，不得凭记忆写 AISec'16 卷期页码。）
- 原件：`raw/papers/methodology/multiple-instance/2016-Pevny-Discriminative-Models-Tree-Structure-MIL-AISec.pdf`
- 证据等级：**全文核验**（题录中的会议信息**待核**）
- 关键位置：摘要；§1 Introduction（提取文本 L70–100）；§3 层次 MIL（L330–400）；§4 实验（L875–935）。
- 核验要点（中文转述）：
  1. **明确把判定单元从流上移到计算机**：「我们绕开这个问题的办法是**把分类对象上移一层**，
     即不再分类单条连接，而是把**计算机（它全部流量的集合）作为整体**来分类。」（§1）
  2. **为什么不能逐流判定——标签粒度所限**（§1）：
     「即使是经验丰富的安全分析员，也几乎不可能判定哪些网络连接由恶意软件发起、
     哪些由良性用户或应用发起」，因为恶意软件常模仿良性连接（作者观察到恶意软件访问
     google.com 做连通性检查、显示广告、发邮件）。因此
     「给单条网络连接打标签之所以不可行，**不只是因为数量巨大，也因为单条连接分类本身有歧义**」。
  3. **实体标签的运维收益**（§3）：「使用计算机等高层实体上的标签，构造训练数据要简单得多」；
     且这种做法「允许把分类器判定以人类可理解的方式解释为**安全事件**，
     **简化了网络管理员的工作**」。
  4. **判定单元的具体定义**（§4）：一个「袋」= 一台计算机在一个 5 分钟窗口内的全部 Web 请求；
     计算机由源 IP **或**代理日志中的用户名标识；子袋 = HTTP 请求中 host 部分相同的请求。
     标签规则：该 5 分钟窗口内只要有一条请求已知由恶意软件引起，该窗口内该计算机即记为受感染。
  5. **实体级不平衡量级**：训练集约 2,000 万台不同计算机（其中 172,013 台受感染）、
     约 8.5 亿条流；测试集约 300 万台计算机（其中 3,000 台受感染）、约 1.2 亿条流；
     即测试数据「大约每一千台干净计算机对应一台受感染计算机」。
- 与本论断关系：**证据类一（判定单元＝计算机，理由同时是标签粒度与运维处置）
  ＋ 类三（单条连接判定有歧义）**。是「为何实体级是可处置告警单元」最直接的一段论证。
- 纳入理由：全文核验，理由陈述明确且带实体级不平衡数字。
- Zotero 状态：待补。
- 待办：**核实正式会议出处与页码**（PDF 内版权行为未填模板）。

### 检查点 3

- 已完成：篇目 1–9 全文核验并落盘（Gehri、Yen、Bilge、Känzig、Hu、Zhang、Lee&Stolfo、
  El Mahdaouy 综述、Pevný）。
- 下一步：本地剩余——Dijk SSRN 序列构造（已初读，待补结果表）、Leoste 2025、Meier 2025、
  DiGennaro 2026、Anderson 2016、Cui 2023 CBSeq、Sun 2024 阈值、Arp 2022 基率谬误；
  然后专攻**反面证据**与联网补齐（Alahmadi 2022、Axelsson 2000、Ho 2021 Hopper、
  Hassan 2019 NoDoze、Clausen 2021 CBAM、Apruzzese 2017）。
- 未关闭疑点：Pevný 会议出处；Yen/Bilge ACSAC 页码。
- 阻塞：无。

---

## 篇目 10 — Dijk, Vaarandi, Meier, Pihelgas（SSRN 预印本，LSPR23/24/25 序列构造）

- 题录：Allard Dijk, Risto Vaarandi, Roland Meier, Mauno Pihelgas.
  "Sequence Construction as a Primary Design Factor in Flow-Based Intrusion Detection:
  A Cross-Year Evaluation on the Locked Shields Datasets."
  SSRN 预印本，https://ssrn.com/abstract=6597680 。
  **PDF 每页页脚明写 "This preprint research paper has not been peer reviewed."**
- 原件：`raw/papers/datasets/LSPR24/ssrn-6597680.pdf`
- 证据等级：**全文核验，但为未经同行评议的预印本**。按仓库规则只能作为设计参考与背景，
  **不得**作为「已发表文献证据」写入正文的核心论断，除非用户明确接受预印本等级。
- 关键位置：摘要与 Highlights；§2.2 相关工作；§4.1.1–4.1.8 八种分组策略；
  §5.3 标注与损失（印刷 p.8 附近）；§6.4 与 §7 讨论（印刷 p.38–39）。
- 核验要点（中文转述）：
  1. **这是本轮找到的唯一一篇把「分组单元」当成主实验变量的受控研究**：
     在 LSPR23/24/25 三个年度数据集上比较八种流序列构造策略（全局时序 OP、5 元组、
     1-IP 主机中心、1-IP 会话、2-IP 主机对、1-Hostname、1-Hostname 会话、2-Hostnames），
     共 485 个配置，模型族含 XGBoost、GRU、Transformer。
  2. **实体对分组在最难的年份上最优**：在正类占比仅 0.44% 的 LSPR25 上，
     Longformer + 2-Hostname 分组取得 AP 0.9411，比 XGBoost 基线高 +0.090 AP；
     Transformer 配置中 2-Hostnames 在三年都领先，优势从 LSPR23 的 +0.006 扩大到
     LSPR24 的 +0.067 再到 LSPR25 的 +0.158。
  3. **关键边界：本文的标注与判定单元仍是「流」**。§5.3 明写
     「分类在流层面进行……预测因而对应结构化序列内的**单条流**，而非聚合的序列级标签」；
     标注也是流级（源或目的 IP 属红队基础设施即为恶意）。
     所以本文支撑的是「**实体上下文改善逐流判定**」，**不是**「实体是判定单元」。
  4. **实体分组改变有效类别平衡**：OP 表示下正类占比约 30.0%（LSPR23）、7.1%（LSPR24）、
     2.2%（LSPR25）；2-Hostname 分组则变为约 0.93%、0.43%、0.44%。
  5. **反面证据（类五）**：
     (a) §4.1.3 明说 1-IP 主机中心分组「把一个 IP 的全部活动串成一条时序流，
         长时间跨度上不相关的事件也会被拼接起来，**可能稀释局部上下文**」。
     (b) §7 讨论：在较容易的 LSPR23/LSPR24 上，「流特征本身已含足够判别结构，
         序列感知模型相对 XGBoost **没有一致收益**」，XGBoost 基线在效率前沿上占优。
     (c) 过细的分组同样有害：5 元组分组把恶意信号稀释到 π ≈ 0.002，表现一致更差
         （π 与最佳 AP 的相关 r = 0.42）。
     (d) 2-Hostnames 的优势**依赖资产身份元数据**；把同样的成对分组逻辑换成裸 IP（2-IP）后，
         LSPR25 上 AP 从 0.94 掉到 0.13。作者强调该映射用的是「哪些端点属于被防护网络」的
         基础设施角色元数据而非流级标签，运维方可从资产台账获得；
         但**没有资产身份元数据时，2-IP 才是更贴近部署现实的替代**。
     (e) 跨年退化：同年 AP 与次年退化的皮尔逊相关 r = −0.87，194 组次年比较中 178 组退化，
         每种分组策略的次年 AP 中位数变化都为负。
  6. **可直接抄用的运维建议**（§7）：作者建议「先取一小组历史上有前景的分组策略，
     把演习初期用于**异常排序与分析员分诊**而不是硬性监督判定，收集分析员核实过的案例
     再做阈值校准或轻量微调」。
- 与本论断关系：**类一（分组单元作为一等设计变量）、类三（实体上下文有用）、
  类五（实体聚合的四条明确代价）**。类五证据最有价值。
- **纳入边界**：预印本 + 判定单元仍为流。引用时必须同时说明这两点。
- Zotero 状态：待补。

---

## 篇目 11 — Anderson & McGrew 2016, AISec'16

- 题录：Blake Anderson, David McGrew. "Identifying Encrypted Malware Traffic with
  Contextual Flow Data." *AISec'16*, October 28, 2016, Vienna, Austria. ACM.
  ISBN 978-1-4503-4573-6/16/10. DOI 10.1145/2996758.2996768. 印刷 pp. 35–46.（版权栏已核）
- 原件：`raw/papers/attack-detection/encrypted/2016-Anderson-Identifying-Encrypted-Malware-Contextual-Flow.pdf`
- 证据等级：**全文核验**
- 关键位置：§1（印刷 p.35–36，contextual flow 定义）；§7 Related Work（印刷 p.43–44）。
- 核验要点（中文转述）：
  1. **实体范围的上下文窗口定义**：把 DNS 上下文流定义为按目的 IP 与该 TLS 流关联的 DNS 响应；
     把 HTTP 上下文流定义为**同一源 IP 在 5 分钟窗口内发出的 HTTP 流**。
     即判定一条加密流时，输入包含同主机近邻流。
  2. **纵向 / 横向关联的术语来源**（§7）：网络侧恶意软件检测有两条主线——
     **纵向关联**用单台主机的流量找感染证据；**横向关联**用两台或更多主机的流量找恶意通信。
     本文属纵向关联。
  3. **反面提示（类五）**：论文指出 BotSniffer、BotMiner 这类横向关联技术
     「**无法有效检出单台受感染主机**」。即跨实体聚合会牺牲单实体检出能力。
  4. 论文同时给出「Because BotFinder is content agnostic…」段落，说明周期性方法
     在只观测 5 分钟短窗口时会失效，而本文方法在短窗口仍可用。
- 与本论断关系：**类三（同主机上下文是必要输入）＋ 类五（跨实体聚合的代价）**。
- Zotero 状态：待补。

---

## 篇目 12 — Cui et al. 2023（CBSeq，通道级 = 主机对粒度）

- 题录：Susu Cui, Cong Dong, Meng Shen, Yuling Liu, Bo Jiang, Zhigang Lu.
  "CBSeq: A Channel-level Behavior Sequence For Encrypted Malware Traffic Detection."
  arXiv:2307.09002v1 [cs.CR], 2023-07-18。**正式期刊出处待核**（PDF 用的是 LaTeX 期刊模板占位页眉）。
- 原件：`raw/papers/attack-detection/encrypted/2023-Cui-CBSeq-Encrypted-Malware.pdf`
- 证据等级：**全文核验**（题录中的正式出处**待核**）
- 关键位置：§I Introduction；§III.A Traffic Granularity（式 (1)–(3)）；§III.B Problem Definition。
- 核验要点（中文转述）：
  1. **形式化的三级粒度定义**（§III.A）：包（单个包，携带五元组、时间、载荷）、
     流（同一五元组或源目的可互换的双向流）、**通道（channel，由一个 IP 对产生的全部流量，
     其内部流集合的源目的 IP 相同或可互换）**。
  2. **判定对象定为通道**（§III.B）：「加密恶意软件流量检测监测**通道流量**是良性还是恶意」。
     §I 明说「通道是把源 IP 与目的 IP 相同的多条流聚合为一个整体，
     **而传统方法通常以流为粒度**；使用通道让我们能更全面地挖掘丰富的行为特征」。
  3. 进一步把行为相似的通道聚成组，用行为序列刻画攻击意图，以提升未知恶意流量检出。
- 与本论断关系：**类一（主机对是判定单元，有形式化定义可引用）**。
- Zotero 状态：待补。
- 待办：核实 CBSeq 的正式期刊出处与卷期页码。

---

## 其他本地命中（已核，证据价值较低，单列备查）

- **Arp et al. 2022, USENIX Security（Dos and Don'ts of ML in Computer Security）**
  原件 `raw/papers/datasets/data-protocol/2022-Arp-Dos-and-Donts-ML-Computer-Security.pdf`。
  P8「基率谬误」条目给出机理与算例：「若可以在 1% 误报下取得 99% 真阳，
  但类别比是 1:100，这实际上意味着**每 99 个真阳伴随 100 个假阳**」。
  可作类二的**机理性**引文，但它讨论的是类别不平衡，**不是**流粒度与实体粒度之别，
  不得当作实体粒度证据。**全文核验**。
- **Sun, Sankararaman, Narayanaswamy 2024（在线自适应异常阈值）**
  原件 `raw/papers/methodology/2024-Sun-Online-Adaptive-Anomaly-Thresholding.pdf`。
  §1 写「误报是有代价的，**每一次检出都需要一位安全运维人员去调查**，
  可能导致『告警疲劳』」；并把分位数 p 的来源之一说成
  「**在不陷入告警疲劳的前提下能被调查的异常率约束**」。
  这是「固定告警预算」提法的直接文献依据，**但同样不区分流与实体粒度**。**全文核验**。
- **Leoste 2025（TalTech 硕士论文，LSPR23/24 上 ML 与 DL 对比）**
  原件 `raw/papers/datasets/LSPR24/2025_Leoste_Comparative_Analysis_ML_DL_LSPR23_LSPR24.pdf`。
  **学位论文，非同行评议会议或期刊**。逐流分类在 LSPR23/24 上准确率超过 99.9%，
  RF 精确率 99.996%（平均 11 个假阳）。可作**类五的弱反证**：在同年同环境下逐流判定的
  误报已经很低。引用时须说明是硕士论文且为同年评估。**全文核验**。
- **Luxemburk & Čejka 2022（细粒度 TLS 服务分类 + 拒识）** arXiv:2202.11984。
  只在评价指标处提到「大量误报导致告警疲劳」，因此只在低 FPR 区间算 AUROC。
  与判定单元无关，**排除**出候选清单。

### 检查点 4（本地穷尽完成）

- 已完成：本地 427 篇（成功提取 417 篇）全部关键词扫描，12 篇重点全文核验并落盘，
  4 篇次要命中已核并说明证据边界。
- **本地缺口（必须联网补）**：
  1. Alahmadi, Axon, Martinovic 2022, USENIX Security 22, "99% False Positives:
     A Qualitative Study of SOC Analysts' Perspectives on Security Alarms", pp. 2783–2800。类二核心。
  2. Axelsson 2000, "The base-rate fallacy and the difficulty of intrusion detection", ACM TISSEC。类二机理原文。
  3. Ho et al. 2021, USENIX Security 21, "Hopper: Modeling and Detecting Lateral Movement", pp. 3093–3110。
     疑为实体（登录事件/主机）判定单元 + 显式告警预算。**待核**。
  4. Hassan et al. 2019, NDSS, "NoDoze: Combatting Threat Alert Fatigue with Automated Provenance Triage"。类二。
  5. Clausen, Grov, Aspinall 2021, *Computers* 10(6):79, "CBAM: A Contextual Model for Network
     Anomaly Detection", doi:10.3390/computers10060079。类三/四。
  6. Apruzzese et al. 2017, "Identifying malicious hosts involved in periodic communications"。类一。**待核**。
  7. **类五反面证据仍不足**：本地只找到「聚合的代价」（Dijk、Zhang、Anderson），
     **没有找到明确主张「逐流判定才是对的」的工作**。需联网专门检索。
- 下一步：联网按上述 7 项检索与下载，命中即落 `raw/papers/` + `wiki/papers/` 笔记 + `INDEX.md`。
- 阻塞：无（待验证网络可用性）。

---

# 联网阶段（2026-08-18）

## 检索式与结果

| # | 查询式 | 结果 |
| --- | --- | --- |
| W1 | `Alahmadi Axon Martinovic "99% False Positives" SOC analysts security alarms USENIX Security 2022` | 命中 USENIX 开放获取 PDF，已下载 |
| W2 | `Hopper modeling and detecting lateral movement USENIX Security 2021 Ho alert budget` | 命中 USENIX 开放获取 PDF，已下载 |
| W3 | `Axelsson "base-rate fallacy" intrusion detection ACM TISSEC 2000 pdf` | 定位 ACM DL，**付费墙，下载返回 HTML，未入库** |
| W4 | `Clausen Grov Aspinall CBAM contextual model network anomaly detection Computers 2021 MDPI` | MDPI 返回 403 Access Denied；退取爱丁堡机构库同作者博士论文 |
| W5 | `intrusion detection "flow-level" versus "host-level" evaluation granularity comparison drawbacks of host-level aggregation IDS` | 命中 Sensors 2024 IP 对粒度论文（已下载）与本地已有 2026 综述 |
| W6 | `"per-flow" detection necessary granularity network intrusion detection critique host-level aggregation hides attacks` | 未命中「主张逐流才对」的论文；命中 FLARE（IoT 评价）等外围 |
| W7 | `"host-level" labeling ambiguity intrusion detection host is both victim and attacker multi-stage CSE-CIC-IDS2018 infiltration limitation` | 命中 CSE-CIC-IDS2018 重标注文档（网页，非论文），记为类五线索 |
| W8 | `Dainotti Pescape Claffy "Issues and future directions in traffic classification" IEEE Network 2012 pdf caida` | 命中作者主页公开 PDF，已下载 |
| W9 | `"host-level" evaluation intrusion detection overestimates performance one malicious flow marks whole host optimistic metric` | 命中 arXiv:2305.01337（Garcia & Valeros），已下载；这是类五最强的直接来源 |
| W10 | `botnet detection "per-flow" granularity required blocking response why not host level aggregation loses attribution` | 未命中同行评议论文明确主张逐流判定；命中专利与外围综述 |
| W11 | `Apruzzese 2017 "Identifying malicious hosts involved in periodic communications" NCA` | 定位 IEEE NCA 2017，**付费墙，未入库** |

## 新入库原件（6 份）

| 路径 | sha256 | 证据等级 |
| --- | --- | --- |
| `raw/papers/methodology/soc-alert-operations/2022-Alahmadi-99-Percent-False-Positives-SOC-Analysts-USENIXSec.pdf` | `bf9a559479c5…` | 全文核验，USENIX Security 22（同行评议） |
| `raw/papers/methodology/soc-alert-operations/2021-Ho-Hopper-Lateral-Movement-USENIXSec.pdf` | `974dce3da2f7…` | 全文核验，USENIX Security 21（同行评议） |
| `raw/papers/attack-detection/entity-granularity/2012-Dainotti-Issues-Future-Directions-Traffic-Classification-IEEE-Network.pdf` | `e474ab60f0d1…` | 全文核验，IEEE Network 26(1)（同行评议） |
| `raw/papers/attack-detection/entity-granularity/2024-Li-End-to-End-NIDS-Contrastive-Learning-IPpair-Granularity-Sensors.pdf` | `2164ff536ae9…` | 全文核验，Sensors 24(7):2122（同行评议） |
| `raw/papers/attack-detection/entity-granularity/2023-Garcia-Towards-Better-Labeling-Process-Network-Security-Datasets-arXiv2305.01337.pdf` | `aedb605821222…` | 全文核验，**arXiv 预印本** |
| `raw/papers/attack-detection/entity-granularity/2022-Clausen-Traffic-Microstructures-Network-Anomaly-Detection-PhD-Edinburgh.pdf` | `1f93978256ad…` | 全文核验（仅核验相关章节），**博士学位论文** |

对应 `wiki/papers/` 笔记 5 篇已建，索引 2 份已更新
（`wiki/papers/methodology/INDEX.md` 新增「告警可处置性与告警预算」小节；
`wiki/papers/attack-detection/INDEX.md` 新增「判定单元与实体粒度」小节）。

## 访问阻塞清单（未入库，须用户手动补或换机构网络）

1. **Axelsson, S. "The Base-Rate Fallacy and the Difficulty of Intrusion Detection."**
   *ACM TISSEC*, Vol. 3, No. 3, August 2000, pp. 186–205. DOI 10.1145/357830.357849。
   出版社页 https://dl.acm.org/doi/10.1145/357830.357849 ，PDF 需订阅。
   建议文件名 `2000-Axelsson-Base-Rate-Fallacy-Intrusion-Detection-TISSEC.pdf`。
   用途：本课题「即使低误报率也会淹没分析员」这一机理的原始出处（现只能间接经 Arp 2022 与 2026 综述引用）。
2. **Clausen, H.; Grov, G.; Aspinall, D. "CBAM: A Contextual Model for Network Anomaly Detection."**
   *Computers* 2021, 10(6), 79. doi:10.3390/computers10060079。开放获取但 MDPI 对本环境返回 403。
   建议文件名 `2021-Clausen-CBAM-Contextual-Network-Anomaly-Computers.pdf`。
3. **Apruzzese, G.; Marchetti, M.; Colajanni, M.; Gambigliani Zoccoli, G.; Guido, A.
   "Identifying malicious hosts involved in periodic communications."**
   *IEEE 16th International Symposium on Network Computing and Applications (NCA)*, 2017。
   页码在不同来源间不一致（dblp 记 11–18，部分引用记 1–8），**入库后必须以原件核定**。
   IEEE Xplore 付费墙。
4. **Hassan, W. U. et al. "NoDoze: Combatting Threat Alert Fatigue with Automated Provenance Triage." NDSS 2019。**
   本轮未尝试下载（时间所限），登记为待补。
5. **SANS Institute. *Common and Best Practices for Security Operations Centers:
   Results of the 2019 SOC Survey*.** 行业报告，非同行评议；若需引用告警量统计需另行评估证据等级。

## 类五（反面证据）检索结论

**明确结论：本轮未检索到任何主张「逐流判定才是正确部署单元」的已发表论文。**
使用的检索式见 W5、W6、W9、W10。这是「未检索到」，**不是「不存在」**。
实际找到的是另一类反面证据——**实体级聚合的代价**，共六条，全部有出处：

1. Zhang 2023 ACSAC §2：聚合信号相比细粒度时间序列**噪声更大**，必须额外引入 EMD 去噪。
2. Dijk SSRN §4.1.3：主机中心分组把一个 IP 的全部活动串成一条时序流，
   长时间跨度上不相关的事件被拼接，**可能稀释局部上下文**。
3. Dijk SSRN §7：在较容易的 LSPR23/LSPR24 上，逐流 XGBoost 基线在效率前沿上占优，
   序列感知模型**没有一致收益**；2-Hostnames 的优势依赖资产身份元数据，换成裸 IP 后
   LSPR25 上 AP 从 0.94 掉到 0.13。
4. Anderson & McGrew 2016 §7：BotSniffer、BotMiner 这类跨主机横向关联技术
   **无法有效检出单台受感染主机**。
5. Garcia & Valeros 2023 §6：**流级指标与 IP 级指标不可互推**；
   流层面 TPR 60%、FPR 10% 的检测器在 IP 层面仍可计为正确检出。
   这条直接约束本课题「425 倍」这一表述的写法。
6. Leoste 2025（硕士论文，弱证据）：LSPR23/24 同年评估下逐流 RF 精确率 99.996%、
   平均仅 11 个假阳，说明「逐流误报必然爆炸」这一说法在同年同环境下不成立。

另有一条**线索级**（非论文，未入库）：CSE-CIC-IDS2018 的 Infiltration 场景中，
同一台主机先作为受害者下载恶意文件、随后作为攻击者发起内网扫描，
使得任何以「受害者 IP」或「攻击者 IP」为键的实体级标注都会失效。
来源为 DistriNet 的重标注文档网页，非同行评议论文，**只作待验证线索**。

### 检查点 5（联网阶段完成）

- 已完成：11 组联网检索、6 份原件入库、5 篇 wiki 笔记、2 份索引更新、5 条阻塞登记。
- 未关闭疑点：Axelsson / CBAM / Apruzzese / NoDoze 未入库；
  Pevný 与 Yen、Bilge 的正式页码待核；CBSeq 正式期刊出处待核。
- 下一步：产出候选证据清单（`候选证据清单.md`）。
- 阻塞：付费墙 3 项，站点反爬 1 项。
