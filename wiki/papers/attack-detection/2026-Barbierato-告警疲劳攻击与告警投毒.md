---
title: "Crying Wolf in Cyberspace: A Cybersecurity Dynamics Study of Alarm Fatigue Attacks（告警疲劳攻击与 alarm poisoning 的随机动力学建模）"
authors: [Enrico Barbierato]
year: 2026
date: 2026-09-11
journal: "Information (MDPI) 2026, 17(5):434，25 页；2026-03-09 投稿 / 2026-04-28 接受 / 2026-05-01 发表；DOI 10.3390/info17050434；CC BY 开放获取"
source_pdf: "[[raw/papers/attack-detection/2026-Barbierato-Crying-Wolf-Alarm-Fatigue-Attacks.pdf]]"
tags:
  - 告警疲劳
  - 告警投毒
  - 可用性攻击
  - 社会技术安全
  - 随机建模
  - 类型/论文
key_finding: "把「**故意注入虚假或误导性告警**」正式命名为 **alarm poisoning**，定义为*「the deliberate injection of false or misleading alerts in order to **increase alarm pressure, erode trust in the monitoring infrastructure, and degrade organizational responsiveness over time**」*（p.1）。并明确与 false data injection 划界：*\"unlike false data injection attacks that manipulate automated estimation or control processes, **alarm poisoning targets the human response layer** by eroding trust and amplifying fatigue\"*（p.4）。用 CTMC + Gillespie 随机模拟（150 次实现、168 h 时域）给出量化结论：在**假告警总强度固定**（`Λ_fake = 1.0 h⁻¹`）下，**高感知严重度**的假告警（Fire–Spam）比**低骚扰型**（Low–Severity Spam）**更快**压垮信任。"
method: "Cyber-security Dynamics 随机建模：四类实体（攻击者 4 个能力级 `A0→A3`、告警基础设施 3 态 `S0/S1/S2`、防御者 3 个姿态 `D0/D1/D2`、员工按 trust×fatigue 分室的人口）构成连续时间马尔可夫链（CTMC），用 Gillespie SSA 精确模拟；蒙特卡洛 3 策略 × 50 次 = 150 次实现，168 h 时域；含复现充分性诊断、单因子敏感性、崩溃阈值稳健性、联合不确定性抽样"
baseline: "三个攻击者策略互为对照（Fire–Spam / Mixed / Low–Severity Spam），**总假告警强度固定**故差异只来自告警类型构成"
aliases:
  - Barbierato2026-告警投毒
  - alarm poisoning
  - 告警疲劳攻击
related:
  - "[[2008-Barreno-机器学习安全与误报可用性攻击]]"
  - "[[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]"
---

# Barbierato：告警疲劳攻击（alarm poisoning）的随机动力学模型

> Enrico Barbierato（天主教圣心大学，Brescia），2026，*Information* 17(5):434，25 页，DOI `10.3390/info17050434` · 原件 `raw/papers/attack-detection/2026-Barbierato-Crying-Wolf-Alarm-Fatigue-Attacks.pdf`

## 证据等级

**本地全文**。原件已下载（2,176,983 字节，SHA-256 `22dac4e0c8663c4e3e33873c85eb384093990bfeb3d6e5d4c3843d9cb57b6f97`，25 页，CC BY 开放获取）；经 MinerU `extract` 转 Markdown 后用 `pypdf` 逐页复核页码锚点（2026-09-11）。**页码即 PDF 页＝印刷页**（页眉逐页核对 `n of 25`）。

**题录更正（登记，防复发）**：本文为**单一作者**（Enrico Barbierato），**不是 "Barbierato et al."**；任务线索中的该写法已作废。本文正文引用文献 [16] 时出现的 "Barbierato et al." 是**该作者的另一篇工作**，与本篇无关。

## 一句话

把「用假告警拖垮人对告警系统的信任」建模成一个可仿真的社会—技术攻击，并给出**在假告警总量固定的前提下，假告警的"构成"本身就能改变崩溃速度**这一量化结论。

## 威胁模型（p.8，§5.1）

模型由四类实体构成（**这是本笔记登记的形式化威胁模型**）：

| 实体 | 状态空间 | 锚点 |
| --- | --- | --- |
| **攻击者** | 四个能力级 `A0→A1→A2→A3`：外部存在 → 立足点 → 作战控制 → **完整告警注入能力** | p.8 |
| **告警基础设施** | 三态 `S0 正常 / S1 被攻陷 / S2 已缓解`；取得立足点后 `S0 --κ_comp--> S1`，缓解生效后 `S1 --κ_mit(D)--> S2` | p.8 |
| **防御者组织** | 三姿态 `D0 监控 / D1 调查 / D2 缓解`；**升级取决于告警压力 `γ_01(Z)`、`γ_12(Z)`**，仅在告警压力充分下降后松弛 `D2 --γ_20--> D0` | p.8 |
| **员工人口** | 按 trust×fatigue 分室的人口计数 `n_{T,F}(t)`，`T∈{0,1,2}`、`F∈{0..F_max}` | p.8 |

- **求解方法（p.8）**：CTMC 用 **Gillespie 随机模拟算法（SSA）精确模拟**，不离散化时间。
- **关键建模选择（p.8）**：防御者升级速率**是告警压力的函数**——即攻击者通过抬高告警压力间接拖慢防御者升级。这是「预算耗尽」在模型里的形式位置。

## alarm poisoning 的正式表述（本笔记核心，供 H 臂威胁建模引用）

| 锚点 | 原文 | 含义 |
| --- | --- | --- |
| **p.1（摘要）** | *"We refer to this adversarial strategy as **alarm poisoning**: the **deliberate injection of false or misleading alerts** in order to **increase alarm pressure, erode trust in the monitoring infrastructure, and degrade organizational responsiveness over time**."* | **最正式的定义**（含"蓄意"限定词 deliberate） |
| **p.4** | *"unlike **false data injection** attacks that manipulate automated estimation or control processes, **alarm poisoning targets the human response layer** by eroding trust and amplifying fatigue."* | **划界**：不是操纵自动化过程，而是针对**人的响应层** |
| **p.24** | *"repeated false alarms can degrade response conditions by increasing fatigue, reducing trust, and pushing the system toward **threshold-like declines in responsiveness**."* | 结论重述：**阈值型**响应退化 |

## 量化指标体系（本笔记登记的第三项）

| 指标 | 定义 | 锚点 |
| --- | --- | --- |
| **time-to-collapse（崩溃时间）** | **低信任比例首次超过 `0.40`** 的时刻（基线定义） | p.13 |
| 崩溃阈值稳健性 | 在 `0.30 / 0.40 / 0.50` 三个低信任阈值下定性排序不变 | p.21（Fig 9） |
| **TRAM LBT（Lagging-Behind Time）** | **防御者到达缓解姿态**与**攻击者到达最高作战阶段**之间的时间差；正值＝防御滞后 | p.22（Fig 10） |
| **alarm pressure `Z(t)`** | 系统级观测量，驱动防御者升级速率 | p.8、p.20（Fig 6c） |
| fatigue（疲劳累积）、low-trust fraction | 员工人口级的宏观观测量 | p.19（Fig 6a/6b） |
| non-collapse runs（未崩溃次数） | 168 h 时域内未达阈值的运行数 | p.21（Fig 9b） |

**实验规模（p.13）**：3 策略 × **50 次独立蒙特卡洛** = **150 次 CTMC 实现**，时域 **168 h**。

## 量化读数（可引的具体数字）

1. **总假告警强度固定（p.13）**：`Λ_fake = 1.0 h⁻¹`，**三个策略的总量相同**，故差异只来自**告警类型构成**。三种构成的概率向量（告警类型顺序为 fire, intruder, server_temp, usb_malware, elevator）：
   - `π_fire = (0.60, 0.15, 0.10, 0.10, 0.05)` —— 强调**安全关键的火警**
   - `π_low = (0.01, 0.04, 0.15, 0.35, 0.45)` —— 集中在**骚扰类与低严重度**告警
   - `π_mixed = (0.05, 0.15, 0.35, 0.25, 0.20)` —— 中间构成
2. **主排序（p.15、p.24）**：`Fire–Spam` **崩溃最快**、`Mixed` 居中、`Low–Severity Spam` **最慢**（且在 168 h 内**最不可靠**）；该排序在 **24 个参数设定中的 22 个**保持不变（p.15、p.23）。
3. **最敏感的参数（p.15、p.23）**：**疲劳恢复率 `φ`**（对中位崩溃时间影响最大，最大位移约 `38%`）；而在 ±25% 扰动下，**控制信任恢复的疲劳衰减系数近乎无效**。
4. **消融（p.16–p.17）**：移除**告警压力反馈**会压缩三策略之间的差距；移除**防御者升级**会提高所有策略的崩溃频率；移除**信任–疲劳耦合**会削弱告警投毒的行为影响。
5. **LBT 的方向性（p.22）**：`Fire–Spam` 常给出**正的** LBT（缓解往往在攻击者已进入最具破坏性阶段之后才到达）；`Low–Severity Spam` 更常给出**负的** LBT。

## ⚠️ 必须随结论转述的限度（作者自述）

- **证据强度是描述性的，不是推断性的（p.22 原文）**：*"the main evidence for strategic differences lies in **descriptive ordering, non-collapse frequencies, and robustness patterns rather than strong inferential separation at the present sample size**."*
- **联合不确定性下排序不稳（p.16）**：在 100 组抽样参数集上，严格基线排序仅在 **21%** 的情形保持。
- **崩溃时间高度随机（p.22）**：*"identical parameter settings can still yield materially different realized trajectories."*
- **人口同质假设（p.23）**：*"The present model assumes a behaviorally homogeneous workforce at the popul..."*（模型假设员工行为同质；p.18 有一个异质暴露的双员工类补充实验）。
- **本文是**仿真研究**，不是真实系统上的测量**：全部读数来自 CTMC/Gillespie 仿真，**没有真实告警数据或真实攻击事件**。

## 可迁移机制

1. **「告警构成」是一个独立于「告警总量」的攻击自由度**（p.13、p.18）：在总量固定下，**高严重度假告警更致命**。对本课题的直接含义是：**只统计误报数量不足以刻画代价，误报的"类型/分数分布"同样重要**——这是**本课题的推论**，本文未如此主张。
2. **防御者升级速率是告警压力的函数**（p.8）：把「预算耗尽」形式化为**速率耦合**，而不是离散的阈值判断。这是把「告警预算」写进模型的现成结构。
3. **阈值型退化 + 高度随机**（p.22、p.23）：结论应作**概率性**而非确定性表述；且**单次运行的读数不代表分布**。这条与本课题「单种子训练 + 配对重采样只量化样本不确定性」的纪律同向。
4. **TRAM LBT 是一个"防御滞后"度量**（p.22）：可用作「检测系统相对攻击者的响应滞后」的量纲参照（本文以**小时**计）。
5. **敏感性分析给出"哪个参数最要紧"**（p.15）：`φ`（疲劳恢复）最敏感——提示在这类建模中，**恢复项往往比累积项更决定结果**。

## 不能直接声称内容

- **不能把 alarm poisoning 等同于「误报注入以掩护真实攻击」**：本文的目标是**侵蚀信任、降低组织响应能力**（社会—技术后果），**没有**建模"真实攻击在噪声掩护下被漏掉"这一路径。后者见 [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]] 向量 2。
- **不能把本文的任何数字搬作本课题的门槛**：`0.40` 低信任阈值、`Λ_fake = 1.0 h⁻¹`、`168 h` 时域、`38%` 位移全部是**该仿真模型的参数化设定**，与检测器的 FPR/FNR 不同量纲。
- **不能声称本文验证了真实攻击**：摘要与正文均只主张 alarm poisoning 是 *"a **credible** socio–technical attack vector"*；无真实数据。
- **不能把三策略排序当作强结论**：作者自述证据为描述性排序（p.22），联合不确定性下仅 21% 保持（p.16）。
- **不能把本文当作「误报注入」这一攻击的**首次**提出**：上位分类学见 [[2008-Barreno-机器学习安全与误报可用性攻击]]（2006/2008 的 Availability attack），面向安全运营的具体向量见 [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]]（2021）。本文（2026）的贡献是**命名 + 随机动力学建模 + 量化**。
- **注意与 false data injection 的区分**（p.4）：本文特意划界，引用时不得把二者混用。

## 与课题的关系

- 本文是本课题威胁模型文献链中**证据等级最高**的一环（同行评议期刊、CC BY、附代码库 `github.com/EBarbierato/ciberattack_fatigue`）——但**它仍是仿真研究，不是真实测量**。
- **三篇的分工（必须分别引用，不得合并）**：

  | 来源 | 层级 | 贡献 |
  | --- | --- | --- |
  | [[2008-Barreno-机器学习安全与误报可用性攻击]] | 上位分类学 | 可用性攻击＝瞄准误报，造成拒绝服务 |
  | [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]] | 面向 SOC 的攻击向量 | 「伪装攻击」：用误报噪声掩盖恶意活动；含"关闭规则"终态 |
  | **本文** | 社会—技术动力学 | **命名 `alarm poisoning`**；把信任/疲劳/告警压力写成可仿真的耦合系统 |

- **差量定位（不变）**：三篇全部停在**威胁建模、攻击向量或影响仿真**；**没有一篇把该威胁模型反用为防御侧的训练信号**。这是本课题 H 臂的机制差量。
- **一处可直接引用的量化先例**：**在假告警总量固定时，告警"构成"仍显著改变崩溃速度**（p.13、p.15）。这是支持「误报的分布形态本身有代价」的现成外部证据——与本课题「干净 FPR 双主轴」的立论方向一致（**这是本课题的关联判断，不是原文主张**）。

## 疑问 / 待验证

- 本文参考文献中与"告警预算"直接相关的来源（如 [2]、[4] 类）**未逐条核验**；若正文要引"告警疲劳普遍性"的数量级，须另找并入库对应来源。
- 模型假设员工行为同质（p.23），异质暴露只在 p.18 有一个双类补充实验；**跨人群的泛化性未充分验证**。
- 附带的代码库 `github.com/EBarbierato/ciberattack_fatigue` **本轮未核验**（未访问、未验证可运行性）；若正文要声称"可复现"，须先核验仓库状态与版本。
- 本文与 [[2021-Drahuntsov-SOC与SIEM误报洪水攻击向量]] **互不引用**（2026 年的本文未引 2021 年那篇），二者的关联是**本课题的判断**。

## 文献信息

- **原件**：`raw/papers/attack-detection/2026-Barbierato-Crying-Wolf-Alarm-Fatigue-Attacks.pdf`（2,176,983 字节，25 页，SHA-256 `22dac4e0c8663c4e3e33873c85eb384093990bfeb3d6e5d4c3843d9cb57b6f97`）
- **来源**：MDPI 出版方开放获取直链 `https://mdpi-res.com/d_attachment/information/information-17-00434/article_deploy/information-17-00434.pdf`（2026-09-11 取得；`www.mdpi.com` 站点返回 403 反爬，改用出版方 CDN 直链）
- **DOI**：`10.3390/info17050434` · ISSN `2078-2489` · 许可 CC BY
- **代码库**：`https://github.com/EBarbierato/ciberattack_fatigue`（**未核验**）
- **转换**：MinerU `extract` 模式，产物在 `/tmp/fp-inject/md/`（一次性中间物，未入库）
