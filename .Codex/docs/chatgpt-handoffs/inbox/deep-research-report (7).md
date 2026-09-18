# 2025–2026 网络安全恶意流量检测公开数据集增量调研

## 结论与筛选口径

检索截止到 **2026 年 9 月 10 日（America/Los_Angeles）**。我把“强推荐”的门槛设得比一般 NIDS 数据集综述更严格：不仅要有 benign/malicious 或攻击类别真值，还要能从公开材料中确认**采集顺序/时间戳和时间跨度**，从而原则上可以构造 “train 早、test 晚” 的前向评测；仅仅 CSV 中有一个 `timestamp` 字段、但官方把所有流随机打散，并不能自动算“跨时间数据集”。

这轮检索的核心结论是：**2025–2026 确实出现了一批新的网络攻击数据集，但增量主要集中在 IoT/IIoT/ICS CyberRange、智能家居和实验室多攻击场景；真正类似 LSPR23/24 那样同时具备“现实运行环境、明确恶意真值、跨较长时间、适合前向验证”的公开新增集极少。** 大多数新数据论文仍然报告随机/分层随机切分的 95%–99.99% 指标，而不是未来期 FPR/FNR。GeNIS 是本轮能最明确核实“恶意标签 + 原始包 + 实际采集日历”的新增项，但它仍是 CyberRange；ICS-NAD 的真实性和 PCAP 价值很高，但其公开可核实材料尚不足以确认一个规范的跨期 forward split。citeturn39search2turn56search0turn58view4

一个很重要的负结果是：**没有检索到可核实的 2025–2026 新“跨年加密恶意流量”公开数据集，能够直接替代你已有的 LSPR23/24。** 加密恶意流量方向 2025 年仍有大量方法论文，但经常继续使用 DataCon2020、CIC-AndMal-2017、CTU/MCFP 等旧数据，而不是释放新的、长期带 malware-family/C2 ground truth 的流量语料。这个缺口与 2025 年最新 NIDS 数据集综述指出的“公开数据质量、真实性和长期适用性不足”是一致的。citeturn39search2

下面的“时间轴”我进一步区分三类：

| 标记 | 含义 |
|---|---|
| **强** | 有明确恶意标签，且公开材料能核实真实采集顺序/日期，可自行构造时间前向划分 |
| **弱/未确认** | 有攻击标签，但只有实验 session、预定义 train/test 或随机切分，不能证明未来期泛化 |
| **仅时间轴** | 时间跨度很好，但标签只是 anomaly/heuristic，不能等价为完整 malicious ground truth |

因此，本轮真正的**强推荐正式候选只有 GeNIS 一项非常明确**；ICS-NAD 我宁愿保守地放在第二档，而不把“real-world”三个字自动等价为“已验证跨时间 benchmark”。

## 强推荐：有恶意标签且有可验证采集时间轴

**GeNIS — GECAD Network Intrusion Scenarios，GECAD / Polytechnic of Porto，Airbus CyberRange。**  
**发布/更新：**Zenodo 数据记录创建于 **2025-02-24**，Data in Brief 数据论文在线发表于 **2025-03-21**；Zenodo 元数据最后修改到 **2026-02-05**，但没有证据表明这次 2026 修改意味着新增了一轮流量采集，因此应把它理解为“2025 数据集、2026 仓库更新”，而不是“GeNIS-2026”。来源：[Zenodo](https://zenodo.org/records/14919237)、[Data in Brief 全文/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11986601/)。citeturn39search7turn39search2

**标签语义：**GeNIS 不是把“异常”粗略当作恶意，而是有明确的场景真值和层次标签。顶层支持 benign/malicious，攻击大类包括 **brute force、DoS、reconnaissance**，并进一步保留攻击子类；原始场景包括 SSH/FTP/SMB brute force、Hulk、ICMP flood、Push&Ack、Slowloris、UDP flood 等，同时单独采集 benign user、benign administrator 和 benign background。官方 `ground-truth` 信息记录每次 capture 的标签及开始/结束时刻。恶意流量是在受控 CyberRange 中实际执行攻击工具产生，属于**真实执行的实验攻击流量**，不是 GAN/SMOTE 生成的合成表格，但也不是野外互联网感染流量。citeturn39search2

**时间结构：**这是其最值得保留的属性。采集明确发生在 **2025-02-06 至 2025-02-12**：正常 user/admin 工作日活动在 2 月 6–7 日，background 在 2 月 8 日周末，攻击场景在 2 月 10–12 日。也就是说，原始 PCAPNG 和 ground-truth 具有真实实验日历和 session 顺序，跨度约一周。可以按日期/session 重新构造前向评测，但需要注意一个严重的设计陷阱：正常流量主要处于早期、攻击主要处于后期，**直接按日期一刀切很可能造成训练集/测试集类别覆盖不对称**；真正严谨的 forward protocol 应先检查每种攻击在 2 月 10–12 日的覆盖，再按攻击 session 或重复场景切，而不是简单“前 70% 时间训练，后 30% 测试”。citeturn39search2turn40view0

**规模与输入：**原始数据约 **37,681,001 packets**；发布方进一步导出了约 **2,806,168 flows**，提供 5、10、30、60 秒等不同 flow interval。仓库文件合计约 **2.5 GB**，其中 packet archive 约 1.0 GB，另有 flow、scenario 和预处理文件。输入形态同时包括 **PCAPNG 原始包、流级 CSV、场景/ground-truth 元数据及预处理特征集**，因此很适合你们自己重跑 Zeek、nPrint、CICFlowMeter、HERA 或自定义 packet-sequence 特征。citeturn39search2turn39search7

**获取与许可：**Zenodo 可以直接下载。论文正文采用 CC BY；但我在可访问的 Zenodo 元数据片段中没有核实到**数据文件本身单独声明的 license 字段**，所以严格记作“**数据许可：未确认；论文许可：CC BY**”，不要因为论文 CC BY 就自动推导所有 PCAP 的许可。citeturn39search2turn39search7

**基线：必须特别警惕。** 官方/后续验证所用 train/test 并不是前向时间划分，而是 **shuffle + stratification**。后续验证中 60 秒 flow 版本里，Random Forest/XGBoost 二分类准确率约 **99.9905%**、F1 约 **99.9949%**，RF/XGB 报告的 FPR 约 **0.1289%**；LGBM、LSTM、MLP 也都接近 99.98%–99.99%。这些数字只能证明“同分布随机流切分很容易”，**不能证明未来三天、未见攻击或跨月份部署性能**。论文没有给出可直接采用的跨时间 FPR/FNR。citeturn40view0

**综合判断：强推荐。** 如果你的目标是“2025 新数据 + PCAP 自提特征 + 能主动设计时间前向实验”，GeNIS 是本轮最干净的新增项之一；但若论文目标明确要求**生产网自然概念漂移**，应把它描述成“时间有序 CyberRange”，不要和 LSPR/ISP 野外时间序列混为一谈。citeturn39search2

## 有恶意标签，但没有可核实的可靠前向时间结构

这一档适合补充攻击类别、PCAP、IoT/ICS 场景或 unseen-family/open-set 实验，但不宜把论文自己的随机精度当成 temporal generalization。

**ICS-NAD — 多真实工业控制系统网络攻击数据集，Xun Zhou 等。**  
**发布/更新：**Science Data Bank 检索结果显示数据记录于 **2025-08-07** 发布；随后论文以 “ICS-NAD: A Dataset Collected in Multiple Real-World Industrial Control Systems for Network Attack Detection” 出现在 **2025 China Automation Congress，2025-09-26 至 09-28**，2026 年又形成 Scientific Data 数据论文 “A dataset collected in real-world industrial control systems for network attack detection”。2026 Scientific Data 的精确上线月份，本次抓取中**未确认**。来源：[Science Data Bank](https://www.scidb.cn/en)、[Nature / Scientific Data](https://www.nature.com/articles/s41597-026-06738-x)。citeturn57search0turn57search4turn57search11turn56search0

**标签语义：**公开论文摘要称数据来自 **三个真实 ICS 品牌/环境**，包含 **20 种常见 ICS 网络攻击类型**、两种攻击流量样本模式，并提供 60 个特征和完整标签。因此它明显优于“仅把偏离正常当 anomaly”的工业数据集；攻击是在实际 ICS 场景中执行和采集，而不是单纯用网络仿真器生成 CSV。citeturn56search0

**时间结构：未确认。** “real-world ICS” 能确认环境真实性，却不能自动证明捕获跨越多天/月或者官方定义了早期训练、后期测试。当前公开检索材料没有让我核实出**精确 capture date、总时间跨度以及是否每种攻击在不同时间段重复出现**。所以这里不把 ICS-NAD 放进严格的第一档；若后续从其 README/metadata 核实出 campaign 时间戳，它很可能是最值得上调的一项。citeturn56search0

**规模与输入：**Scientific Data 摘要报告数据总量约 **245.96 GB**，同时包含 **原始 ICS PCAP** 与带标签的 **CSV 特征**，这是本轮新数据中极突出的 PCAP 资产。citeturn56search0

**获取与许可：**论文说明公开发布，数据记录可从 Science Data Bank 获取；**确切数据 license、本次是否无需登录直下、单文件清单及镜像策略均待核**。citeturn57search0turn56search0

**基线：**数据论文称用约 10 个 ML/DL 分类器做验证，但我没有从当前可访问资料中核实到独立“未来期”FPR/FNR；因此不要把这些分类实验理解成 temporal baseline。**跨期/未见攻击基线：待核。** citeturn56search0

**综合判断：高价值、条件强推荐。** 若你的优先级是“**真实 ICS + 245 GB 原始 PCAP + 完整攻击标签**”，其优先级甚至可以高于 GeNIS；但如果实验主问题是 drift/forward generalization，目前还缺一个关键时间元数据确认。citeturn56search0

**TRUSTLab Dataset — IoT/edge 入侵流量，TRUSTLab。**  
**发布：2026-05-05**，对应 Frontiers in Computer Science 论文。来源：[Frontiers 全文](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2026.1803271/full)，数据 DOI：`10.82432/10317/21203`。citeturn58view4turn26view0

它包含 **benign + 15 个攻击家族/类别**，覆盖 DDoS、DoS、port scan、brute force、Web/API 攻击、DNS amplification/tunneling/spoofing/DGA、MitM、evasion、TLS/SSL 相关攻击、exploitation、exfiltration、buffer overflow、Slowloris、C2/beaconing 等，协议面包括 HTTP(S)、DNS、邮件、SSH、SNMP、NTP、MySQL 以及 REST/GraphQL/SOAP API。攻击是 VirtualBox 隔离实验环境中通过真实攻击脚本/工具执行的，属于**实验室真实执行攻击**。citeturn25view0turn26view3

规模约 **4.6 million bidirectional flows**，每条使用 CICFlowMeter 风格约 80 个特征，发布组织为 16 个单类 CSV。论文的采集流水线先通过 SPAN/packet capture 获得包，再转成 CICFlowMeter flow；不过我没有核实到数据仓库是否把**全部原始 PCAP 一并公开**，所以“PCAP 可获取”记为 **未确认**，不能仅凭实验方法中“抓过 PCAP”就认定仓库提供 PCAP。citeturn26view0turn26view3

时间上，它更像 session/campaign 数据：常规攻击 session 约 **5–10 分钟**，慢速类别可到 **15–30 分钟**。每个 session 单独只包含 benign 或一种 attack family，这有利于避免流标签污染，但并不形成自然的跨月/跨年概念漂移时间线。citeturn26view3

其基线尤其值得当“反例”记录：采用 **80/20 stratified bi-flow split**，而非时间前向切分。测试中约 1,034,194 flows，记录了 TP **567,844**、FN **30,018**、TN **359,053**、FP **77,279**；attack recall 约 **0.9498**、precision **0.8802**、specificity **0.8229**、accuracy **0.8963**、ROC-AUC **0.9676**。系统级第二阶段可把假警率从约 7.5% 压到约 2.2%，但这些都不是“未来月份”性能。citeturn26view4

**获取/许可：**论文为开放获取；数据通过独立仓库 DOI 发布。数据文件自己的许可条款本次**未确认**。因此，TRUSTLab 很适合“多攻击类别、DNS tunnel/C2/API 等现代攻击面”的同环境监督学习，但不满足严格 temporal benchmark。citeturn58view4turn26view0

**Smart Home Intrusion Detection Dataset — Vipin Das / Binoy Nair, Amrita Vishwa Vidyapeetham。**  
Mendeley Data v1 **2026-01-14** 发布，数据 DOI `10.17632/x95b37z2vy.1`；对应 Data in Brief 论文发表于 **2026-04**。来源：[Mendeley Data](https://data.mendeley.com/datasets/x95b37z2vy/1)。citeturn58view3turn20search4

数据的亮点不是攻击种类数量，而是**七个 multi-stage attack scenarios**：一个 scenario 中可以连续包含不同攻击步骤，更接近 kill-chain/multi-stage IDS，而不是把每个 attack primitive 独立打成一张表。攻击仍然是在受控智能家居实验环境中实际执行；七个场景每一步的完整攻击类型映射，本次可访问元数据没有全部展开，故细粒度语义记作**待核**。citeturn58view3turn20search1

总计 **178,831 samples**，发布方给出的 train/test 为 **148,959 / 29,872**。仓库明确包含网络捕获的 **PCAP**，并提供 Python 脚本将其提取成 CSV 特征，因此原始包重特征工程能力很好。citeturn20search1turn58view3

**时间结构：**multi-stage 顺序是有的，但我没有核实到独立的日历跨度，亦没有证据表明官方 train/test 是按真实时间“早→晚”切。因此这里把它归为“有攻击序列、无可靠长期时间轴”。官方预定义 train/test 也不能自动视为 temporal split。citeturn20search1turn58view3

**许可/获取：**Mendeley 可公开下载，明确为 **CC BY 4.0**，是本轮许可最清楚的新 PCAP 数据之一。**未来期 FPR/FNR：未见报告；官方实验不应当作跨时间证据。** citeturn58view3

**DataSense: CIC IIoT Dataset 2025 — Canadian Institute for Cybersecurity / UNB。**  
来源为 CIC 官方：[DataSense: CIC IIoT Dataset 2025](https://www.unb.ca/cic/datasets/iiot-dataset-2025.html)；下载通过 CIC 表单：[DataSense download form](https://cicresearch.ca/IOTDataset/Datasense/)。公开页面确认 2025 年发布，对应 Firouzi 等在 *Electronics* 2025 的 DataSense 论文；**精确发布月份本次官方页面未核实，记“2025，月份待核”**。citeturn54view0turn55view1

这是一个较现代的 **IIoT synchronized sensor + network stream** 数据集：约 40 个互联设备、15 种以上工业传感器，并同时包含 IoT、edge、网络设备和攻击机。攻击总计 **50 种**，归入七类：reconnaissance、DoS、DDoS、Web exploitation、MITM、brute force、malware。恶意标签来自受控实验中主动执行的攻击 campaign。citeturn54view0

官方页面给出的 packet 量级很大：benign 约 **259,212 packets / 12 小时**；DDoS 14 种攻击约 **1.142 billion packets**；DoS 14 种约 **537.5 million**；recon 约 **15.79 million**；Web 攻击约 **589,958**；MITM 约 **125.66 million**；恶意软件部分包含 Mirai SYN/UDP flood。Web 类明确包括 backdoor upload、command injection、SQL injection、blind SQLi 和 XSS；MITM 还包括 ARP spoofing/impersonation/IP spoofing。citeturn54view0

**时间结构：**官方强调 synchronized time-series，benign 段至少有 12 小时；但当前材料没有给出让我能够核实的整体日历跨度，也没有证明 50 种攻击在多个自然时期重复采集。因此，它适合时序模型和 session-level holdout，却暂时不能当成“跨时期概念漂移”标准集。citeturn54view0

**输入：**网络 packet/stream 与 sensor/log 数据都存在，但本次官方抓取没有让我确认下载包中是否公开**原始 PCAP 文件**，故 PCAP 项严格写 **未确认**。**获取方式**需要填写姓名、邮箱、机构、职位、国家等表单信息；表单说明这些信息用于 CIC 统计。**数据许可条款：未确认。** citeturn55view1turn54view0

论文做了较广泛 ML/DL 和 feature-selection 基线，但本次没有核实到规范的 future-period FPR/FNR。因而最合理的定位是：“**规模大、攻击面新、IIoT 多模态很有价值；跨时间证据不足**”。citeturn54view0

**Gotham Dataset 2025 — Cardiff 等团队的可复现大规模 IoT 网络数据集。**  
论文/数据说明于 **2025-02-05** 公开，来源：[arXiv](https://arxiv.org/abs/2502.03134)。论文明确说明数据公开于 Zenodo，但本轮没有可靠解析出对应 Zenodo record ID，因此**精确仓库 URL、总文件大小和 dataset license 待核**。citeturn46view0

Gotham testbed 含 **78 个 emulated IoT devices**，协议包括 MQTT、CoAP、RTSP；每台 IoT 设备流量在 gateway-device 接口处分别抓取。攻击是脚本化真实执行，包括 **DoS、Telnet brute force、network scanning、CoAP amplification，以及多个 C&C communication stages**。这使它在“低层 IoT 流量 + C2 + CoAP”这一块比传统 CICIDS 更贴近现代 IoT 环境。citeturn46view0

**输入形态很强：原始 PCAP + 标注 CSV。** 抓包用 tcpdump，后续以 Tshark/Python 进行 feature extraction 和标签生成。它特别适合 packet sequence、自提 TLS/flow/timing 特征或研究 C2 stage。citeturn46view0

**时间结构：**当前论文摘要能确认按设备、按攻击场景独立采集，但不能确认自然跨天/月演化，也没有规范 forward split，所以仍放第二档。2026 年针对 Gotham 的比较研究报告 RF F1 可达到约 **0.99**，但公开描述没有建立这是跨时间结果；因此应视为同环境高分，而不是部署期证据。citeturn47academia1turn46view0

## 有时间轴，但缺可靠恶意真值

**MAWIFlow Benchmark — 2025-06。**  
论文 “MAWIFlow Benchmark: Realistic Flow-Based Evaluation for Network Intrusion Detection” 于 **2025-06-20** 公开。来源：[arXiv](https://arxiv.org/abs/2506.17041)。它是本轮非常值得关注的**时间漂移 benchmark**，但严格说并不满足你的“完整 malicious ground truth”标准。citeturn58view2

MAWIFlow 从 MAWI/MAWILab 原始互联网 backbone traffic 构建 CICFlowMeter 风格 flow，并尽量保留 MAWILab 的原有 anomaly labels。数据取自真实跨太平洋 backbone，抽取了时间上明确分离的 **2011-01、2016-01、2021-01** 样本，因此天然可以做 **2011→2016→2021** 的 forward/generalization 实验。和 GeNIS 的一周 CyberRange 相比，这里的时间漂移是真正跨五年尺度的互联网环境变化。citeturn58view2

问题也同样明显：**MAWILab label 是异常检测/自动分析体系的 anomaly label，并不等价于已人工验证的“恶意攻击家族真值”**。某个 flow 被判异常，不能自动解释为 malware C2、DDoS 或某个 ATT&CK technique。因此，MAWIFlow 很适合研究 temporal concept drift、模型老化、FPR 稳定性，却不适合直接作为“恶意家族监督分类”gold standard。citeturn58view2

论文确实把跨年份性能变化作为核心实验，并观察到传统 tree-based 模型随时间推移明显退化，而 CNN-BiLSTM 一类模型相对稳定；这比绝大多数 2025/2026 新 NIDS 数据论文的随机 split 更贴近你的评测诉求。**精确逐年 FPR/FNR 数值本次可访问文本未完全核实，故数字项记“待核”，不编造。** citeturn58view2

**规模、精确 repository URL 与 license：本次解析未确认。** 论文说明公开了数据集、构建 pipeline 和模型实现。由于其基础 PCAP 来自 MAWI/MAWILab，使用时还需要分别检查 MAWI 原始数据和二次发布 benchmark 的条款。citeturn58view2

**CESNET-TimeSeries24 / CESNET-QUICEXT-25 的“恶意补标注”核查。** 这两项你已明确列为已有基线，所以这里不重复推荐。本轮针对 2025–2026 的第三方 attack-ground-truth、malware-family labels、IOC enrichment 等做了定向检索，**没有发现可以核实为公开发布的新恶意真值版本**。尤其 TimeSeries24 本身仍是约 40 周、约 27.5 万 IP 的真实 CESNET3 ISP 时间序列，时间结构非常好，但原始目标是流量预测/异常分析，而不是提供攻击真值。结论应表述为“**本次未检索到补标版**”，而不是断言不存在任何私人/未索引项目。citeturn56academia4

这也揭示了目前数据生态里一个很典型的断层：**真实 ISP 数据容易拥有长时间轴，但难有完整 malicious ground truth；完整恶意标签容易在 CyberRange 获得，但持续时间通常只有小时到数天。** GeNIS、DataSense 与 MAWIFlow 恰好代表了这个三角权衡。citeturn39search2turn54view0turn58view2

## LSPR25、经典来源与“新版本”核查

**LSPR25：演习存在，但截至检索截止日没有核实到可公开获取的数据集版本。** NATO CCDCOE 官方材料确认 **Locked Shields Partners Run 2025** 确实举行，继续使用高强度、现实化的 cyber exercise 环境；因此“LSPR25”不是误传或不存在的版本名。citeturn33search0turn33search1

但是，针对 “LSPR25 dataset / Locked Shields Partners Run 25 / LSPR 2025 Zenodo” 等组合检索时，我**没有找到一个能像 LSPR24 那样核实 DOI、公开文件列表、license、标签定义和下载入口的正式数据记录**。相反，公开可验证的最新 LSPR 数据记录仍然是你已经有的 **LSPR24**：其 Zenodo/publication 记录在 2025 年公开可见。citeturn29search1turn29search19

因此截至 **2026-09-10**，最稳妥的研究表述是：

> **LSPR25 演习：已确认；LSPR25 public dataset：本次检索未确认。不能把论文/帖子中提到 “LSPR25” 直接当成已经发布的数据集。LSPR24 仍是本轮能完整验证的最新公开 LSPR 数据版本。**

这点尤其值得写进论文 dataset-selection section，因为网络检索里已经有二手文献把 “LSPR24/LSPR25 intrusion detection datasets” 并列提及，但二手引用本身不能替代原始 dataset DOI/data card。

**Malware Capture Facility / Stratosphere。** MCFP 仍然是持续活跃的真实 malware traffic 来源，其项目持续采集恶意软件及正常流量，恶意侧包括实际感染产生的 C&C 通信；这对 encrypted C2/malware-family PCAP 依然很有价值。来源：[Malware Capture Facility Project](https://www.stratosphereips.org/datasets-malware)。citeturn29search2

不过，本轮没有核实出一个满足你要求的**“2025 或 2026 单独版本化发布 + 精确月份 + 完整 supervised label schema + 统一许可 + 官方 forward split”**的新年度 MCFP benchmark。因此我没有把“2025/2026 新增的若干 capture”硬凑成一个新候选数据集。更适合的用法是：以 MCFP 为**滚动式恶意 PCAP 池**，自己按 capture date 和 malware family 构造时间外测试，而不是把整个站点当作“MCFP-2026 dataset”。citeturn29search2

**MAWI/MAWILab。** 经典 MAWI 长期 archive 的优势仍是自然时间变化；2025 真正形成“新 benchmark 增量”的，是上面列出的 **MAWIFlow**，而不是突然出现了一个带人工 malicious ground truth 的 MAWI-2025。citeturn58view2

**CTU/Stratosphere 旧数据的“网页新日期”需排雷。** 例如 CTU-SME-11 在部分 2025 网页索引中看起来像新项目，但其数据实际早在 **2023-07-30** 已通过 Zenodo 发布。因此不能把网页最近修改时间或 2025 年新论文引用误判成“2025 新数据集”。citeturn16search3

**本轮顶会核查。** 针对 NDSS、IEEE S&P、USENIX Security、CCS、RAID、IMC 等 2025–2026 论文做公开数据关键词搜索后，本轮能够**完整核实为新公开监督恶意流量集**的条目，反而主要来自 Data in Brief、Scientific Data、CIC 和专门的数据论文，而不是上述安全顶会直接发布的 standalone benchmark。这里应理解为“本轮检索结果”，不是声称这些顶会绝对没有任何新 capture artifact。

## 排除项与待核观察名单

下面这些项目值得知道，但我不把它们计入正式候选，原因分别是“尚无法验证 public data card”“任务不属于网络流量监督检测”或“缺关键元数据”。

| 条目 | 2025–2026 状态 | 为什么不计正式候选 |
|---|---|---|
| **MedSec-25** | 2026 论文明确使用，Kaggle 搜索结果可见 “MedSec-25: IoMT Cybersecurity Dataset” | 很相关的 IoMT 攻击数据，论文报告 macro-F1 约 97.83%；但本轮未核实规模、PCAP/flow 形态、完整攻击列表、capture span 和 license，因此只能列“待核” citeturn49search1turn51academia0 |
| **Labelled IoT flow-based network traffic dataset for cyberattack detection** | 2026 Data in Brief 项目被学术索引收录 | 描述显示有 PCAPNG、flow、9 scenarios/6 categories，标签由 campaign 时间窗口 + attacker IP 生成；但本轮未取得可核实的原始公开 repository/license 页面，故不冒充已确认 public candidate |
| **BigFlow-NIDS** | 2026 Data in Brief 文献条目可检索 | 声称约 66.9M NetFlows、55 attributes、32 attack categories、CSV/Parquet，但原始来源、是否聚合旧集、实际 public repository/license 没有被本轮一手资料充分核实；先不计入 citeturn42search0 |
| **End-to-end threat hunting multiclass dataset** | 2026 新论文 | 论文称 >7M labeled packets、15 类攻击、实验室环境且决策树约 99.9% accuracy；公开数据入口与时间结构没有充分验证，所以不计 |
| **UL-ECE-\*-H-IoT2025** | 2026 学位/论文材料中介绍的一组 2025 healthcare-IoT 攻击数据 | DDoS/MITM/selective-forwarding 等由 Cooja/ns-3 生成，但没有核实到稳定公共 repository 与许可；且合成网络成分较高 citeturn42academia4 |
| **2025 XAI encrypted-malware custom set** | 2025 论文称 1,127 unique connections、54 malware families | 对你的 encrypted-malware 任务高度相关，但没有核实到真正开放的数据仓库；模型在 custom set 上报告约 99% 指标也没有可验证跨时间协议，因此不计 |
| **QUT-DV25** | 2025，新 14,271 PyPI package 动态执行语料 | 有动态 sandbox 的 network 行为，但 supervision 主体是**软件包/供应链恶意样本**，并混合 syscall/eBPF/resource telemetry，不是你要求的网络流量级 IDS benchmark，故范围外 citeturn44academia2 |
| **CIC-Trap4Phish 2025** | 2025 CIC 新数据 | 主要是 Word/Excel/PDF/HTML/QR/URL 等 phishing artifact，而非网络 PCAP/flow，按你的硬性范围应排除 citeturn13search2 |
| **CIC-YNU-IoTMal** | 有 2025/26 公开页面 | 你已经明确列为已有基线，本报告不重复推荐 |

其中 **MedSec-25** 和 **2026 labelled IoT flow dataset** 是我认为最值得继续盯的两个“可能升档”项目：前者因为 IoMT + 现代 edge deployment，后者因为公开描述里存在 **PCAPNG + campaign timestamp ground truth**。但在缺许可证、正式 repository metadata 或完整 capture chronology 时，把它们写成“已验证公开新数据集”反而会降低调研可信度。

另外，对于那些只提供随机 train/test、然后宣称 99.9% accuracy 的新 NIDS 数据论文，本报告**没有因为年份新就自动收录**。GeNIS、TRUSTLab、Gotham 等之所以仍被列，是因为它们至少带来新 PCAP、新攻击面、新网络环境或可重新划分的 session 元数据；其论文随机基线则被明确降权。citeturn40view0turn26view4turn46view0

## 2025–2026 发布趋势判断

**最明显的增长点是 IoT/IIoT/ICS，而不是通用企业互联网恶意流量。** GeNIS 模拟 SME 网络，DataSense 聚焦 IIoT，Gotham 聚焦 MQTT/CoAP/RTSP IoT，TRUSTLab 加入 IoT/edge/API/DNS/C2，Smart Home 数据专门研究 multi-stage attacks，ICS-NAD 则把规模推到真实工业系统和约 246 GB PCAP。换言之，2025–2026 新数据的“场景真实性”更多通过**搭建复杂物理/虚拟 CyberRange 并实际发动攻击**实现，而不是通过长期监控生产互联网并事后获得高质量攻击真值。citeturn39search2turn54view0turn46view0turn58view4turn58view3turn56search0

**原始 PCAP 的情况反而比前几年有所改善。** GeNIS 明确发 PCAPNG，Gotham 发 PCAP + CSV，Smart Home Mendeley 数据明确带 PCAP，ICS-NAD 的 Scientific Data 描述则包括约 245.96 GB 的 PCAP + CSV。对于研究 raw-byte、packet-size/time sequence、TLS/QUIC handshake、flow exporter bias 或自定义 Zeek/nPrint 特征，这是比只发 CICFlowMeter CSV 更有意义的增量。citeturn39search2turn46view0turn58view3turn56search0

**攻击语义正在从“DoS/scan/bruteforce 三件套”向更多 stage 和应用层行为扩展。** Gotham 有 C&C stages 与 CoAP amplification；TRUSTLab 包括 DNS tunneling/DGA、C2/beaconing、API attacks、exfiltration/evasion；Smart Home 直接把多个攻击步骤组织为 multi-stage scenario；DataSense 同时覆盖 malware、MITM、Web exploitation 和 Mirai。这个趋势对“未见攻击类型”研究是积极的，因为可以把一个完整 family/scenario 从训练集中移除，而不是只做随机流 holdout。citeturn46view0turn26view3turn58view3turn54view0

但**论文的评测协议没有同步进步**。GeNIS 的发布版 train/test 是 shuffle+stratified，TRUSTLab 是 80/20 stratified flow split；Gotham 的后续高 F1 也没有建立成跨期 benchmark。换句话说，“数据本身带 session/timestamp”与“论文真正检验 temporal drift”仍是两件事。2025 的 MAWIFlow 是少数把 2011→2016→2021 时间漂移直接摆上实验台的项目，但它又牺牲了最重要的一点——其 MAWILab anomaly label 不是完整 malicious-family ground truth。citeturn40view0turn26view4turn58view2

**最枯竭的子方向仍然是“真实、长期、加密、带恶意家族真值”的流量。** 2025 年加密恶意流量研究继续活跃，特别关注 TLS 1.3、QUIC/HTTP-3、DoH、encrypted C2 等，但很多工作仍复用旧的 DataCon、CIC-AndMal、CTU/MCFP 等语料；在本轮新发布数据中，没有出现一个能够明确取代 LSPR23/24、同时提供跨年 chronology、malware/C2 family ground truth 和原始 encrypted PCAP 的公开 benchmark。MCFP 仍有真实恶意 C2 capture 的长期价值，MAWI/CESNET 仍有真实时间轴优势，却分别缺统一年度 benchmark 或完整恶意标签。citeturn29search2turn56academia4

因此，如果目的是搭一个 **2026 可发表的 temporal malicious-traffic benchmark**，本轮新数据最现实的组合不是寻找某个“完美单集”，而是按不同评价面组合：**GeNIS** 负责 2025 原始 PCAP、attack-session chronology 和可重做前向 split；**ICS-NAD** 负责真实 ICS、超大 PCAP 和多攻击类型，但时间跨度需先核实；**TRUSTLab / Gotham / Smart Home / DataSense** 负责 unseen attack、C2/DNS tunnel、multi-stage、IoT/IIoT 扩展面；**MAWIFlow** 单独负责长期 temporal drift，但必须把标签称为 anomaly 而非 malware ground truth。citeturn39search2turn56search0turn58view4turn46view0turn58view3turn54view0turn58view2

最终优先级可以压缩成：

| 优先级 | 数据集 | 恶意真值 | 时间前向潜力 | 原始 PCAP | 最适合的论文评价面 |
|---|---|---:|---:|---:|---|
| **A** | **GeNIS** | ✅ 完整层次标签 | ✅ 2025-02-06→12；需自行重切 | ✅ PCAPNG | temporal/session holdout、raw traffic、未见 attack scenario |
| **A− / 待时间核实** | **ICS-NAD** | ✅ 20 attack types | △ span 未确认 | ✅，约 245.96 GB 总数据 | real ICS、cross-system、raw PCAP |
| **B+** | **TRUSTLab** | ✅ 15 attack families | △ session only | △ 仓库 PCAP 待核 | C2/DNS tunnel/API、FPR 分析 |
| **B+** | **Smart Home 2026** | ✅ 7 multi-stage scenarios | △ scenario order | ✅ | multi-stage / unseen scenario |
| **B** | **DataSense 2025** | ✅ 50 attacks / 7 categories | △ synchronized sequence、总 span 待核 | △ | IIoT、多模态、Mirai/MITM/Web |
| **B** | **Gotham 2025** | ✅ benign + scripted attacks/C2 | △ scenario/session | ✅ | IoT、CoAP、C&C stage、raw packet model |
| **C-temporal** | **MAWIFlow 2025** | ❌ anomaly ≠ 完整 malicious truth | ✅ 2011→2016→2021 | 基于 MAWI 原始 PCAP | 长期 drift / model aging |
| **不计入** | **LSPR25** | — | — | — | 演习已确认，但截至 2026-09-10 未核实公开 dataset release |

如果把你的既有基线 LSPR23/24 视作参照系，那么 **2025–2026 的真正新增价值并不是出现了一个“LSPR25 替代者”，而是出现了几批更容易拿到原始 PCAP、攻击场景更现代的 IoT/ICS 数据；而“跨年加密恶意真值”这一最关键的 benchmark 空缺，到了 2026 年 9 月仍然没有被公开数据生态真正填上。** citeturn33search0turn29search1turn39search2turn56search0