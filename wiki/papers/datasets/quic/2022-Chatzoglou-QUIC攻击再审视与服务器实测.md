---
title: "Revisiting QUIC attacks: a comprehensive review on QUIC security and a hands-on study"
authors: [Efstratios Chatzoglou, Vasileios Kouliaridis, Georgios Karopoulos, Georgios Kambourakis]
year: 2022
date: 2026-08-13
journal: "International Journal of Information Security (IJIS)，第 22 卷（2023），第 347–365 页；在线发表 2022-12-02"
source_pdf: "[[raw/papers/datasets/quic/task-landscape/2022-Chatzoglou-Revisiting-QUIC-Attacks-IJIS.pdf]]"
doi: "10.1007/s10207-022-00630-6"
tags:
  - QUIC
  - HTTP3
  - 攻击分类学
  - 模糊测试
  - 拒绝服务
  - 零日漏洞
  - 类型/论文
aliases:
  - Chatzoglou2022-QUIC攻击再审视
  - Revisiting QUIC attacks
key_finding: "对六个主流生产级 QUIC 服务器（OpenLiteSpeed、Caddy、NGINX、H2O、IIS 10、Cloudflare/quiche）各做 24 小时模糊测试（两个 fuzzer 各 12 小时，累计约 43,200 与 4,320,000 个种子），共发现 5 类可复现问题；其中 QUIC-loris 低速攻击只需每秒 2–3 个包（1 分钟约 150–200 个包）即把 Caddy 的 CPU 打到 99.3%–99.9%，已分配 CVE-2022-30591（表 3，p.360；§5.2.5，p.361）。QUIC 攻击被归纳为密码学、握手、模糊测试、传输层、隐私五类（图 2，p.351）。"
method: "两部分：(1) QUIC 安全文献综述，按五类建立攻击分类学；(2) 在 Azure 云上部署六个支持 HTTP/3 的生产级服务器，用 Mutiny-fuzzer（Radamsa 变异，1 种子/秒）与 Fuzzotron（Blab 变异，100 种子/秒）各测 12 小时，配合每秒一次 HTTP 探活脚本与 Wireshark 定位触发种子，再人工构造 PoC 复现"
baseline: "六个服务器实现互为横向对照；无机器学习实验、无数据集、无检测模型"
related:
  - "[[2021-Zhan-早期QUIC流量的网站指纹识别]]"
  - "[[2022-Wang-CoMPS连接迁移流量拆分隐私防御]]"
  - "[[H23Q-HTTP3与QUIC攻击数据集]]"
  - "[[2022-AlBakhat-QUIC流量入侵检测机器学习方法]]"
---

# QUIC 攻击再审视：安全综述与服务器实测

> Chatzoglou、Kouliaridis、Kambourakis（希腊爱琴大学信息与通信系统工程系）与 Karopoulos（欧盟委员会联合研究中心 JRC，意大利 Ispra），IJIS 22:347–365，在线发表 2022-12-02，开放获取（CC BY 4.0）。
> 无资助（Funding 声明，p.362）。数据与代码：作者称 PoC 托管在 `https://github.com/efchatz/QUIC-attacks`，论文录用后转公开（脚注 16，p.360）。

## 一句话

这是本批四篇里唯一**不做流量分析**的一篇：它给出的是 QUIC 侧「有哪些攻击、攻击长什么样、真实服务器实现有多脆」的地图，对本课题的价值在于**任务定义与标签语义**（我们要检测的 QUIC 恶意行为具体是哪些），而不是检测方法或指标参照。

## 论文的两个目标（摘要，p.347）

1. 第一份（作者自称）覆盖 QUIC 安全的全面文献综述。
2. 对当时六个最主流的生产级 QUIC 服务器做实测安全评估，找到若干可快速耗尽服务器资源的零日漏洞。

作者的总判断是：QUIC 的碎片化生产级实现尚不成熟（摘要，p.347）。

## 攻击分类学（§4，图 2，p.351）

全文把 QUIC/gQUIC 相关攻击分为五类。这是本笔记中对本课题最有结构价值的部分：

| 类别 | 代表攻击 | 出处 |
| --- | --- | --- |
| 密码学（Cryptographic） | Bleichenbacher / PKCS#1 v1.5 预言机、DROWN 的 MitM 变体（针对 gQUIC 的 server config 消息）、nonce 复用、Selfie 反射攻击 | §4.1，p.351–353 |
| 握手（Handshake） | 重放攻击、包篡改（CID/stk 未受保护导致降级到 TCP+TLS）、crypto stream offset 注入、0-RTT 相关、版本协商与 SCSV 降级、CID 枚举（load balancer 后实例数泄露）、state-overflow 与反射放大 | §4.2，p.353–356 |
| 模糊测试（Fuzzing） | 形式化规约生成的随机测试器、DPIFuzz（重复包号、重叠 stream offset） | §4.3，p.355–356 |
| 传输层（Transport-layer） | 有状态防火墙的 UDP 打洞绕过（Linux conntrack 5 元组假设） | §4.4，p.356 |
| 隐私（Privacy） | QUIC 服务分类（CNN + RF 识别 Google 服务）、TLS 1.3 会话恢复的可关联性、MIMIQ 连接迁移防御、网站指纹（含本批 Zhan 与 Ludovic 两篇） | §4.5，p.356–357 |

分类学中若干可直接引用的量化点：

- DROWN 的 gQUIC MitM 变体需要 2^17 次 SSLv2 连接与 2^58 次离线计算（§4.1，p.352）。DROWN 通用版需被动观察约 1K 个 RSA 密钥交换的 TLS 会话、发起 40K 次 TLS v2 连接、做 2^50 次对称加密运算（p.352）。
- 2048 位 RSA 下 Bleichenbacher 攻击需 2,120 次查询、合计 66 秒（p.352）。
- CID 枚举攻击：对 15 个 QUIC 实现的分析中 25% 存在此问题（ATS、Chromium、LiteSpeed、ngtcp2）（§4.2，p.356）。作者随即指出 Chromium 与 ngtcp2 并非负载均衡器，因此该攻击对二者实际不可行。
- Nawrocki 等人从 UCSD Network Telescope 分析 **92 M 个 QUIC 包**，筛选条件为「> 25 个包、时长 > 60 秒、任一 1 分钟窗口的最大包速率 > 0.5 pps」，识别出 **2,905 次攻击，占全部响应会话的 11%**；其中 98% 针对知名 QUIC 服务器（§4.2，p.354）。作者转述的另外两个观察：QUIC 洪泛比 TCP/ICMP 洪泛更短但平均严重程度相当；QUIC 洪泛通常是多向量攻击的一部分，与 TCP/ICMP 洪泛高度相关。
- 同一工作的复现实验：不支持 RETRY 防护的服务器在 100 pps / 10,000 pps 下响应变慢 32% / 64%（4 或 128 workers）；启用 RETRY 的服务器仅用 4 个 worker 即可承受 100,000 pps（§4.2，p.355）。
- Van 等人的 QUIC 服务分类：捕获约 150 GB 真实流量、超过 20K 条流、五类 Google 服务，准确率约 99%（§4.5，p.356）。**注意这是流量分类，不是恶意检测。**
- MIMIQ：每 25 到 100 个包做一次连接迁移可把网站指纹攻击准确率压到 10% 以下（§4.5，p.357）。
- Ludovic 等人：网络层填充防御下仍能以 F1 > 92% 识别网站；其混合数据集只含 4% QUIC 流量，因此另建了 70% QUIC 占比的数据集（§4.5，p.357）。

## 实测部分（§5，p.357–361）

### 测试床（表 2，p.358）

| 服务器 | 操作系统 | 规格 | 版本 |
| --- | --- | --- | --- |
| OpenLiteSpeed | Ubuntu 18.04 | 1 CPU / 1 GB RAM | 1.7.15 |
| Caddy | Ubuntu 18.04 | 1 CPU / 1 GB RAM | 2.4.6 |
| NGINX | Ubuntu 18.04 | 2 CPU / 4 GB RAM | 1.21.7 |
| H2O | Ubuntu 18.04 | 1 CPU / 1 GB RAM | 2.3.0-DEV |
| IIS | Windows Server 2022 | 2 CPU / 4 GB RAM | 10 |
| Cloudflare | Ubuntu 18.04 | 2 CPU / 4 GB RAM | 1.16.1 |

选取依据为 W3Techs 2022 年 4 月的份额数据中同时支持 QUIC 与 HTTP/3 的服务器；Apache 因当时不支持 QUIC 被排除（§5，p.357）。每台服务器只存一个简单 HTML 页面。

### 模糊测试方法（§5.2.1，p.359）

- Mutiny-fuzzer（Cisco Talos）+ Radamsa 变异器，测试速率 1 种子/秒。
- Fuzzotron + Blab 变异器，测试速率 100 种子/秒。
- 每个服务器每个 fuzzer 各测 12 小时，合计 24 小时/服务器；累计约 **43,200**（Mutiny）与 **4,320,000**（Fuzzotron）个种子。
- 监控：自制 Python3 脚本每 1 秒请求一次页面，响应超过 5 秒即记录时间戳，再用后台 Wireshark v3.6.5 回溯匹配触发种子。
- 未评估 IP 欺骗，因为 Azure 虚机自带反欺骗防护（p.359）。

### 结果（表 3，p.360）

| 攻击 | OpenLiteSpeed | Caddy | NGINX | H2O | IIS | Cloudflare | 合计 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QUIC-fuzz | ✓(0/1 Fuzzotron) | ✓(1/1 Mutiny) | ✓(0/1 Fuzzotron) | ✓(1/0) | ✓(1/2) | ✗ | 5 |
| QUIC-downgrade | – | – | – | – | – | – | – |
| QUIC-out-of-joint | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 3 |
| QUIC-loris | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | 1 |
| QUIC-encapsulation | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | 1 |
| QUIC-flooding | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 3 |
| 合计 | 1 | 5 | 3 | 3 | 1 | 0 | – |

（括号内两个数字分别为人工与自动模糊测试发现的问题数；QUIC-downgrade 取决于客户端与服务端是否都支持 gQUIC，故未打勾叉。）

### 各攻击的可观测特征（对标签定义最有用的部分）

- **QUIC-fuzz**（§5.2.2，p.359–360）：攻击者只需发送约 **30 个包**，受影响服务器（H2O、IIS 10、Caddy）分别出现 **6 秒、3 秒、6 秒**的响应延迟，且延迟持续 **10–30 分钟**。作者强调攻击不稳定：PoC 对每个服务器各测 20 次，受影响服务器约 **25%** 的情况被击中；把包数提高到 300 结果相同。作者推测该攻击影响服务器的消息解析器，类似应用层哈希碰撞攻击。
- **QUIC-downgrade**（§5.2.3，p.360–361）：W3Techs 数据显示当时约 **7.9%** 的网站支持 gQUIC，含 YouTube、Gmail。识别方式是窃听 `alt-svc` 头（gQUIC 版本形如 `Q0**`，如 Q050、Q046、Q043）。作者实测 Chrome 30.x–80.x 在 Win7/Win10 虚机上均未真正以 gQUIC 连接（始终回落 HTTP/2 over TCP），因此**判定该攻击实践上不可行**，但建议服务器下线 gQUIC。
- **QUIC-out-of-joint**（§5.2.4，p.361）：与 frame mangling 同源，fuzzer 能在 TLS 握手期间或 HTTP 服务期间向服务器传入任意 QUIC 包；Caddy、H2O、NGINX 三者受影响。
- **QUIC-loris**（§5.2.5，p.361）：低速慢攻。1 分钟内约 **150–200 个包**（2–3 包/秒）；具体做法是发起约 **100 条并行 QUIC 连接**，握手完成后 1 秒内即丢弃，等约 **30 秒**再重新发起握手。受害者取一个基础 HTML 页需要 **超过 20 秒、有时超过 1 分钟**，CPU 持续超过 **99%**。根因经 Caddy 团队与 quic-go 团队确认：plpmtud（Packetization Layer Path MTU Discovery）的探测计时器溢出，取值超过 **100 K**，因为攻击者在握手完成后立即断连使 quic-go 无法发送 Path MTU Discovery 包，此后 CPU 立刻打到 **99.3%–99.9%**。已按协同漏洞披露流程报送，分配 **CVE-2022-30591**。
- **QUIC-encapsulation**（§5.2.6，p.361）：把 TCP 包塞进 UDP、或 UDP 塞 UDP，非请求发送。多数情况无影响，但 Caddy 有时会回一个 TCP keepalive probe 或 UDP 包，作者认为这可能带来防火墙绕过或 SSRF 机会。
- **QUIC-flooding**（§5.2.7，p.361）：持续用 **0-RTT 连接**攻击显著抬高 CPU；影响 Caddy、NGINX、H2O。**100 条并行 0-RTT 连接、单个攻击实例**即足够。NGINX 是唯一被暂时瘫痪的：攻击发起后约 **15 秒**（2–3 轮）服务器失去响应约 **30 秒**，且每次攻击都可复现，即攻击者可每 **15–20 秒**拆掉全部在途连接。Caddy 的 CPU 几乎瞬间到 **99.9%**。H2O 出现超过 **3 秒**的 HTTP 响应延迟。作者指出单个攻击者即可吃掉服务器至少 **五分之一** 的 CPU，故可 DDoS 化；缓解手段是启用 QUIC 的 RETRY 特性。

### 生态碎片化数据（表 1，p.349）

作者列出 GitHub 星标 ≥ 100 且同时支持服务端与客户端的 **18 个** QUIC 库，涉及 **7 种**编程语言与 **9 个**（结论节写作 7 个）TLS 库。星标数（2022-05-19）前列为 quic-go 6.7K（GO，Caddy/NextDNS 使用）、quiche 6.1K（Rust，Cloudflare/curl）、nghttp2 4K、msquic 2.8K（Windows 10/11、Windows Server 2022）、quinn 2.1K。作者的推论是：单个实现中的漏洞未必影响其他实现，每个实现必须单独评估。

**注意论文内部不一致**：表 1 的列头标注 TLS 库有 9 个唯一值，而结论节（p.362）写「7 different TLS libraries」。

## 与本课题的关系

第 1 点是原结论的引用边界，第 2–4 点为本课题推论。

1. **可直接引用的**：(a) QUIC 攻击的五类分类学（图 2，p.351）；(b) 六个生产级 QUIC 服务器实测出的五类可复现问题与 CVE-2022-30591（表 3，p.360；§5.2.5，p.361）；(c) QUIC 实现生态碎片化的量化描述（18 个实现 / 7 种语言，表 1，p.349）；(d) 从网络望远镜数据中观察到 QUIC 洪泛占响应会话的 11%（转述 Nawrocki 等人，p.354）。**不可引用为**任何检测方法、检测性能或数据集的来源——本文不训练任何模型，不发布流量数据集。

2. **对本课题的主要用途是「任务与标签定义」，而不是方法或指标**。若本课题后续要在 QUIC 上定义恶意流量标签，本文给出了标签空间的候选清单及其**可观测代价**，这一点比分类学本身更有用：

   | 攻击 | 攻击者代价 | 流量层可观测形态 | 出处 |
   | --- | --- | --- | --- |
   | QUIC-loris | 2–3 包/秒，100 条并行连接 | **极低速率**，握手完成后立即断连并周期性重来（约 30 秒周期） | §5.2.5，p.361 |
   | QUIC-flooding | 100 条并行 0-RTT 连接 | 大量 0-RTT 连接建立 | §5.2.7，p.361 |
   | QUIC-fuzz | 约 30 个畸形包 | 极少量畸形包，效果延迟 10–30 分钟且只有 25% 命中率 | §5.2.2，p.360 |

   **这三条对本课题的直接含义**：QUIC-loris 与 QUIC-fuzz 都是**低速率、低包量**的攻击，与 [[2025-Kadi-QUIC时代入侵检测机器学习适配]] 中 GET Flood / Connection Flood / Scan 三类**高速率**攻击形成互补。如果本课题要论证「基于流量的 QUIC 恶意检测存在空白」，本文提供的是「有一批真实存在、已分配 CVE 的低速攻击，其流量足迹在体量特征上与正常流量难以区分」——这类攻击恰恰是逐流统计特征最容易漏掉、而**实体级时间维度聚合**最可能捕获的（周期约 30 秒的握手-断连循环是一个明确的实体级节律）。此为推论，本文未做任何检测实验。

3. **对「实体级聚合」的间接支持（推论）**：QUIC-loris 的定义本身就是实体级的——单条连接看不出异常（正常握手、正常断开），异常只存在于「同一攻击者发起的 100 条并行连接 + 30 秒周期重复」这一聚合层面。这与本课题从逐流 AP 0.22 到实体级 AP 0.52–0.55 的落差是同类结构：**攻击语义天然定义在实体上，而不是流上**。可与既核验的 Känzig 2019、Gehri 2023、Kadi 2025 三点并列，作为「实体级评价缺位」论证的第四个证据点；但需注意本文是**攻击定义层**的证据（攻击本身就跨多条连接），不是评价协议层的证据（本文根本没有评价协议）。

4. **对跨年度迁移的相关性：低**。本文无任何漂移、迁移或时间维度的实验。唯一相关的观察是生态碎片化——18 个实现、版本演进快（论文中多处提到实现在 draft v18–v30 之间行为不同）意味着**QUIC 流量的年际分布变化可能比 TCP 更剧烈**，因为协议实现本身在变。这是一个值得记录但完全未经验证的假设。

## 局限与需注意的边界

- 本文**不是流量分析论文**：无数据集、无标注、无模型、无指标。任何把其中数字当作检测性能的引用都是错误的。
- 实测部分的稳定性弱：QUIC-fuzz 只有约 25% 的复现率（p.360），作者自己承认「更稳定的版本才会对线上基础设施构成严重威胁」。
- 服务器规格差异较大（1 CPU/1 GB 到 2 CPU/4 GB，表 2），跨服务器的 CPU 占用与延迟数字不完全可比。作者未讨论此混淆因素。
- 未评估 IP 欺骗（Azure 反欺骗保护，p.359）；作者在未来方向中把「QUIC 对 IP 欺骗的抵抗力」列为完全未被研究的方向（§6，p.362）。
- 作者列出的其他未被研究方向（§6，p.362）：QUIC 上的缓存投毒；有状态 QUIC fuzzer；DoQ / SMBoverQUIC / P2PoverQUIC / RTPoverQUIC 的安全模型；专用的 QUIC 包构造工具（当时仅 aioquic 可部分胜任）。

## 未在原件中定位到的项

- **QUIC-fuzz 各服务器具体触发种子的内容与数量**：只给出受影响服务器与延迟秒数，未给出种子样本。
- **PoC 仓库的可访问性**：脚注 16（p.360）称仓库当时为私有，录用后公开；本次未核验其当前可访问状态。
- **表 3 中 QUIC-fuzz 一列括号数字的完整含义**：表注说明第一、第二个数字分别为人工与自动模糊测试发现的问题数，但 H2O 的 `✓(1/0)` 与 IIS 的 `✓(1/2)` 未标注使用了哪个 fuzzer（其余三个标了 ✫/✸ 符号）。
- **TLS 库数量的内部不一致**：表 1 列头标 9，结论节（p.362）写 7，全文未解释。
- **各攻击的服务端资源基线**：正常负载下六个服务器的 CPU 占用与响应时间未报告，因此攻击造成的相对增量无法精确计算。

## 可引用的逐字原文（≤15 词）

- 实现成熟度判断：`"the fragmented production-level implementations of this contemporary protocol are not yet mature enough"`（摘要，p.347）。

## 文献信息

- DOI：<https://doi.org/10.1007/s10207-022-00630-6>
- 开放获取：CC BY 4.0（p.362）
- 本地 PDF：`raw/papers/datasets/quic/task-landscape/2022-Chatzoglou-Revisiting-QUIC-Attacks-IJIS.pdf`（19 页）
- 本地 PDF SHA-256：`c69b4cf4820834f58a3fbf7bd565d3a77aa0563e87d454b014702a6714b0bcea`
- 阅读方式：`pdftotext -layout` 全文 1,144 行逐节通读。表 1、表 2、表 3 在文本层可完整提取；图 2（攻击分类学）与图 3（模糊测试流程）为图像，本笔记中的分类学结构取自正文 §4 各小节标题与叙述。
