---
title: "ReACKed QUICer: Measuring the Performance of Instant Acknowledgments in QUIC Handshakes"
authors: [Jonas Mücke, Marcin Nawrocki, Raphael Hiesgen, Thomas C. Schmidt, Matthias Wählisch]
year: 2024
date: 2026-08-13
journal: "Proceedings of the 2024 ACM Internet Measurement Conference (IMC '24), 2024 年 11 月 4–6 日, 西班牙马德里, ACM, 12 页"
source_pdf: "[[raw/papers/datasets/quic/citing/2024-Muecke-ReACKed-QUICer-Instant-ACK-QUIC-Handshakes-IMC.pdf]]"
doi: "10.1145/3646547.3689022"
tags:
  - QUIC
  - 握手性能
  - CDN
  - 受控测量方法
  - 实现异质性
  - 类型/论文
aliases:
  - Muecke2024-InstantACK
  - ReACKed QUICer
  - QUIC 即时 ACK 测量
key_finding: "同一个协议优化（即时 ACK）在不同丢包位置上给出方向相反的结论：第二个客户端 flight 丢失时 TTFB 中位数改善 10–28 ms，而第一个服务器 flight 的后续报文丢失时 TTFB 反而恶化约 177–188 ms（§4.2）；八个 QUIC 实现中至少三个（picoquic、mvfst、quiche）不按预期响应即时 ACK，作者据此断言协议级结论不能由单一实现得出（§4.1、§5）。与本课题的关系是方法论层面：它是「机制有效性必须按场景分面报告、不能只报聚合均值」的干净范例。"
method: "QUIC Interop Runner 容器化测试床，八个客户端实现对一个改造过的 quic-go 服务器；不用随机丢包率而是定点丢弃特定 UDP 数据报并按「等信息量丢失」对齐；配合 1M Tranco 域名的主动扫描与自建 Cloudflare 免费层域名的一周持续观测"
baseline: "同一测试床内 IACK（即时 ACK）与 WFC（等待证书）两种服务器行为互为对照；每组配置重复 100 次；RTT 覆盖 1/9/20/100/300 ms；证书 1212 B 与 5113 B 两档（后者超过防放大限制）"
related:
  - "[[QUIC互操作运行器与公开qlog归档]]"
  - "[[qlog与解密PCAP的观测边界]]"
  - "[[EPIQ-QUIC实现多样性qlog数据集]]"
  - "[[2023-Luxemburk-QUIC细粒度服务分类与周级数据漂移]]"
---

# QUIC 即时 ACK 握手性能测量

> Mücke（TU Dresden）、Nawrocki（NETSCOUT）、Hiesgen（HAW Hamburg）、Schmidt（HAW Hamburg）、Wählisch（TU Dresden），IMC '24，12 页，CC-BY 4.0（p.1）。
>
> **原件状态（必读）**：`raw/` 中的这份 PDF 交叉引用表损坏（`pdfinfo` 报 `Couldn't find trailer dictionary`，文件末尾无 `%%EOF`，为截断下载）。`pdftotext`、`pypdf`、`pdfminer.six` 三种常规路径全部失败。本笔记的正文来自**逐内容流 zlib 解压 + TJ/Tj 文本算子还原**，覆盖到摘要、正文全部六节、参考文献与附录 C–F。还原文本丢失连字（ffi/fi/ff 显示为空格），故本笔记中的引用逐字原文只取不含连字的片段。**因此本笔记按节号（§）定位，不按印刷页码定位**——还原出的内容流顺序与印刷页并非一一对应。

## 一句话

这是一篇标准的 IMC 式受控测量：把一个具体的服务器行为（收到 ClientHello 后立刻回 ACK，不等证书）放进可控测试床，穷举丢包位置、RTT 与证书大小，得到的结论不是「这个优化好」或「不好」，而是**一张按场景分格的结论表**（附录 C 表 2），并且明确指出结论在部分客户端实现上被实现缺陷污染。

## 问题设定

- CDN 常见部署把 TLS 端点与证书库分离，前端服务器要现取证书（§2）。前端有两个选择：
  - **WFC（wait for certificate）**：等证书到手再回第一个包。客户端由此估到的 RTT 被证书取回延迟 `δC` 撑大。
  - **IACK（instant ACK）**：立刻回一个 ACK，证书到手再发 ServerHello。
- 后果链条：QUIC 的 PTO（Probe Timeout）用第一个 RTT 样本的 3 倍初始化，且 **PTO 初始化时忽略 ACK 中携带的 acknowledgment delay 字段**（§2）。所以要给客户端一个准确的初始 PTO，唯一手段就是即时 ACK（§5）。
- 论文的六项贡献里与本课题相关的是第 (5) 项：**通过比较不同实现与数值分析，判定改善来自协议层面而非实现层面**（§1 贡献列表）。

## 测量方法（本笔记要借的部分）

- 测试床：QUIC Interop Runner（QIR），容器化互操作测试框架，同时采集 pcap 与 qlog（§3）。qlog 含 `recovery:metrics`（平滑 RTT、RTT 方差），但各实现暴露频率与完整度不同（§3、附录 E）。
- **不用随机丢包率**。作者显式反对「随机丢包比例」与「选定真实部署」两种常见做法，改为**定点丢弃特定数据报**，理由是 QUIC 允许多个 QUIC 包合并进一个 UDP 数据报，各实现合并程度不同，同一个「丢第 2 个数据报」在不同实现上丢掉的信息量并不相同（§3）。于是作者先逐包解析每个实现的合并方式（附录 E 表 4 给出每个实现的第二个客户端 flight 占用哪几个数据报），再**按等信息量丢失对齐**后比较。
- 参数网格：文件 10 KB 与 10 MB；证书 1212 B（可 1-RTT 完成）与 5113 B（超过防放大限制）；单向时延 0.5–150 ms 组成的对称 RTT；带宽固定 10 Mbit/s；每个测试重复 **100 次**；前后端延迟由服务器代码里的可配置 sleep 模拟（§3）。
- 客户端八实现：aioquic、go-x-net、mvfst、neqo、ngtcp2、picoquic、quic-go、quiche；服务器为改造支持 IACK 的 quic-go（§3）。
- 野外测量：QScanner 对 2024-08-06 的 Tranco Top 1M 做 QUIC 握手 + HTTP/3 HEAD，连续三天重复；另在 Cloudflare 免费层挂 12 个自有域名（默认配置，证书由 Cloudflare 托管、Google Trust Services 签发），其中 6 个每分钟 1 次连接、6 个每分钟 60 次连接，另选 6 个 Tranco Top 1000 的 Cloudflare 域名对照，跑一周；观测点为汉堡（DE）大学网 + 洛杉矶、圣保罗、香港三个 Google Cloud VM（§3）。
- 两处防混淆控制值得抄：只保留与探测点同城的应答（用 Cloudflare 的 `Cf-Ray` 头里的 IATA 码判断），以排除更大范围的网络效应；只保留含首个 ACK 的应答，以排除丢包（§3）。

## 关键数字（按节号定位）

### 一、无丢包基线

- IACK 与 WFC 之间的延迟差（由客户端上报）中位数：neqo 2.9 ms 到 mvfst 7.8 ms；go-x-net 例外，个体测量波动大（中位 0.1 ms 到 12.7 ms）且部分数值有误（§4.1）。
- 计入默认 PTO 与错误 PTO 计算后，RTT 从 1 ms 到 300 ms、每档 100 次测量，IACK 相对 WFC 的**中位 PTO 改善在 7 ms 到 24.7 ms 之间**（§4.1）。
- 证书超过防放大限制（5113 B）+ 200 ms 前后端延迟、无丢包时，TTFB 中位数改善最大的是 neqo（9.6 ms）与 ngtcp2（10 ms）（§4.1、图 5）。
- 反例：quiche 在启用 IACK 时表现变差，因为它把对 PING 帧的应答连同合并包一起当作无效丢弃（§4.1）。go-x-net 的平滑 RTT 初始化错误（报告 RTT 33 ms 但平滑 RTT 初始化为 90 ms）（§4.1）。

### 二、丢包场景（结论反转的地方）

| 场景 | 谁更好 | 幅度 | 出处 |
| --- | --- | --- | --- |
| 第一个服务器 flight 的后续数据报丢失 | **WFC 更好** | IACK 多花 177 ms（go-x-net）到 188 ms（neqo）才收到首个载荷 | §4.2、图 6 |
| 第二个客户端 flight 丢失 | **IACK 更好** | 首字节中位数提前 10 ms（mvfst）、11 ms（aioquic、quic-go）、12 ms（neqo、ngtcp2）、23 ms（quiche）、28 ms（go-x-net） | §4.2、图 7 |

机制解释（§4.2）：服务器发出的 IACK 本身不是 ACK-eliciting 的，因此服务器收到客户端探测包时拿不到新的 RTT 样本，只能退回默认 PTO；WFC 的首包合并了 ACK+ServerHello，ServerHello 必须被确认，服务器因此拿得到 RTT 样本。**同一机制在一个丢包位置上是优势、在另一个位置上是劣势。**

作者还指出相对收益随 RTT 缩放：改善的绝对值跨 RTT 基本恒定，但相对影响在短 RTT 下更大，例如 quiche 在 9 ms 网络时延下改善了 2.3 个 RTT（§4.2）。

### 三、野外部署（§4.3 表 1，Tranco Top 1M）

| CDN | 域名数 | 启用 IACK 比例 | 跨测量最大差异 |
| --- | --- | --- | --- |
| Akamai | 533 | 32.2% | 12.9% |
| Amazon | 4338 | 41.0% | 18.0% |
| Cloudflare | 247407 | 99.9% | 0.1% |
| Fastly | 3960 | 0.0% | 0.0% |
| Google | 6062 | 11.5% | 11.5% |
| Meta | 112 | 0.0% | 0.0% |
| Microsoft | 34 | 0.0% | 0.0% |
| Others（主机托管） | 26404 | 21.5% | 2.3% |

- IACK 比 ServerHello 平均提前到达的中位值：Cloudflare 3.2 ms、Amazon 6.4 ms、Google 30.3 ms、Akamai 20.9 ms（§4.3，跨全部观测点）。
- 自有 Cloudflare 域名：与 Tranco 域名同速率访问时几乎总收到 IACK（99.9%）；提高访问频率后收到合并 ACK+SH 的比例升到 7.5%，作者视为证书缓存的强指示（§4.3）。
- 若 Cloudflare 改用 WFC，PTO 将被撑大 6.3–7.2 ms，最高达中位 RTT 的 79%（§4.3）。
- Tranco 选样中合并 ACK+SH 的比例差异极大：discord.com 91.9%、cloudflare.com 50.5%、tinyurl.com 17.7%、docker.com 0.7%（§4.3）。

### 四、实现异质性（附录 E 表 4）

八个实现的默认 PTO：aioquic 200 ms、go-x-net 999 ms、mvfst 100 ms、neqo 300 ms、ngtcp2 300 ms、picoquic 250 ms、quic-go 200 ms、quiche 999 ms——RFC 9000 建议值是 1 s，绝大多数实现显著偏离（附录 E 表 4）。第二个客户端 flight 占用的数据报索引也各不相同（quiche 只占 1 个，picoquic 占 4 个）。

附录 D 表 3 记录 16 个服务器实现在 Initial 包中报告的首个 ACK Delay：6 个报 0 ms，msquic 根本不发 Initial/Handshake ACK，其余在 0.4 ms（quinn）到 15.2 ms（s2n-quic）之间，s2n-quic 报告的延迟甚至超过连接 RTT。

### 五、结论表（附录 C 表 2）

作者最终不给单一结论，而给一张二维表：行是「证书大小是否超过防放大限制」，列是「无丢包 / 第一个服务器 flight 除首个数据报外丢失 / 第二个客户端 flight 丢失」和 `δC` 是否超过 3×RTT。证书小于防放大限制时四格里有三格推荐 IACK、一格推荐 WFC；证书超过限制时四格全推荐 IACK。

## 与本课题的关系

论文本身与加密恶意流量检测无关，不提供 (a)(b)(c) 三类证据中的任何一类。它的价值是**方法论**，以下均为本课题推论。

1. **不可引用为**任何与检测性能、漂移或聚合有关的结论。这篇是传输层握手性能测量。若在论文中出现，只能出现在「QUIC 侧受控测量方法」或「实现异质性影响可观测量」的位置。

2. **可迁移机制一：拒绝聚合均值，改报分面结论表**。本文的核心动作是把「IACK 好不好」拆成「丢包位置 × 证书大小 × δC 相对 RTT」的格子，每格给出方向。本课题当前的困难分面（跨年度、实体类型、攻击阶段、流长度）同样存在方向相反的可能：实体级 AP 0.5233–0.5475 是聚合数字，掩盖了哪些实体类型上有效、哪些无效。**待补的最小实验**：按实体度数（2-IP 对涉及的流数）分箱，逐箱报告 DR@4%FPR，看聚合收益是否集中在少数高度数实体上。这是推论，未验证。

3. **可迁移机制二：等信息量对照，而不是等参数对照**。作者不用「都丢第 2 个数据报」，因为不同实现在第 2 个数据报里装的信息不同；他们先测清各实现的合并方式，再按信息对齐。本课题的对应问题是**共同预算基线**：比较 XGBoost、MLP、前缀均值、RWKV-7 状态递归时，「同样的 epoch 数」或「同样的参数量」都不是等信息量对照，真正需要对齐的是每个模型实际能看到的历史信息范围。当前「因果前缀均值 ctx=cumsum(h)/cumsum(mask)」与「完整 RWKV-7 状态递归」的比较是否等信息量，值得按本文思路显式论证。

4. **可迁移机制三：把实现/工具缺陷当作一等公民报告**。本文有三处：quiche 的连接 ID 重复退休导致测量中止、go-x-net 的平滑 RTT 初始化错误、aioquic 用了不同的 RTT 方差公式（附录 E）。作者没有剔除这些点，而是分别标注并解释其对结论的影响。本课题在报告「完整 RWKV-7 状态递归反而更差」时应采取同样姿态：先排除实现缺陷（状态在 batch/流边界是否正确重置、mask 是否正确传播），并把排查过程写进笔记，而不是直接把它当作机制结论。

5. **重复次数与方差**：每格 100 次重复，且关键图（图 5、图 6、图 7）逐次测量点全画出来而不是只画中位数。本课题当前「单种子方差大（0.1848–0.2879）」的状态，与本文的做法差距明显；在给出任何机制结论前需要补多种子。

## 可引用的逐字原文（≤15 词）

- 关于丢包建模：“Our emulation instead simulates particular datagram losses to better understand root causes”（§3）。
- 关于结论方向反转：“In this scenario, WFC outperforms IACK”（§4.2）。
- 关于客户端可靠性：“multiple implementations processed instant ACKs incorrectly, which added delays”（§5）。

## 未在原件中定位的项

- **印刷页码**：因交叉引用表损坏，无法建立还原文本与印刷页的可靠映射。本笔记全部按节号与附录编号定位。
- 图 4–13 的曲线数值：还原文本只含图题、图注与坐标刻度标签，图内数据点未核读。本笔记引用的所有数值均取自正文或表格文字。
- 附录 A、B 的内容：还原文本中未出现（可能位于被截断的部分或未被识别为文本内容流）。附录 C–F 可读。
- 数据与代码地址：还原文本中未出现制品发布链接。

## 文献信息

- DOI：<https://doi.org/10.1145/3646547.3689022>
- ACM ISBN：979-8-4007-0592-2/24/11（p.1 版权块）
- 本地 PDF：`raw/papers/datasets/quic/citing/2024-Muecke-ReACKed-QUICer-Instant-ACK-QUIC-Handshakes-IMC.pdf`（**文件截断，xref 损坏**）
- SHA-256：`8539afecdd0129c12e0c355ca5294bec3f81bd09f5b14e5d85d7d60d22c39779`
- 建议动作：重新获取完整原件后，用 `pdftotext` 复核本笔记全部数值并补上印刷页码。
