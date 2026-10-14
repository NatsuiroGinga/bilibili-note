# 核验笔记：标签可靠性（噪声感知）建模在时间漂移安全检测中的文献核验

- 任务日期：2026-10-14
- **权威副本**：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/.Codex/docs/2026-10-14-标签可靠性文献核验/notes.md`
- 本文件为第二副本（任务抬头指定的 `ch3-lamda-20260908` 工作树），与权威副本内容一致。
- **最终报告不落盘**（harness 禁止子代理写 report 文件），由本代理在最终回复正文给出。

---

## 工具可用性（实测，决定覆盖面）

| 工具 | 状态 | 后果 |
| --- | --- | --- |
| **Bash** | **不可用** | 无法跑 `literature_search` CLI、`curl` OpenAlex、下载 PDF 到 `raw/papers/` |
| 本地混合索引 CLI | 不可用 | 替代：`Grep` 对 `wiki/**/*.md` **词法**检索（**向量通道未运行**） |
| `WebFetch` | **全环境无外网** | 不能直连 OpenAlex / 抓 HTML 全文 |
| **`WebSearch`** | **可用** | 在线候选发现主通路 |
| **Zotero MCP** | **可用**（PDF 级联有服务端外网） | **唯一可取得在线论文全文的通道** |
| `Write` report 文件 | **被 harness 禁止** | 报告改由回复正文承载 |

## C1 · 本地词法检索（Grep over `wiki/`）

关键词：`label noise|noisy label|标签噪声|噪声标签|label reliability|annotation quality|weak supervision`；`VirusTotal|vt_detection`

- **LAMDA 附录 F 表 13：2017 年 5.19% 原恶意样本当前被判良性**（`wiki/papers/datasets/2026-Haque-LAMDA-…md:91`）→ Q3/Q4，本地全文
- **Prasse 2017 ECML Table 1**：VT 5–7 月后重查仅 **0.16%** 原恶意翻转（`wiki/papers/methodology/multiple-instance/2017-Prasse-加密流量LSTM恶意软件检测-ECML.md:37,53`）→ Q4，本地全文
- **Arp 2022 十大陷阱 P2 = Label Inaccuracy**（`datasets/data-protocol/2022-Arp-…md:45`）→ Q4，本地全文
- **RTTAD 2026 附录 D**：co-teaching 抗伪标签噪声（`attack-detection/2026-Huang-RTTAD-…全文.md:287,299`）→ Q1/Q2，本地全文
- 2023 Zhang 校园网 VT **检出滞后**（`:144`）；TESSERACT `p≥4`+13% 灰件；BAYWATCH 任一引擎报恶 → Q4
- SoRR 2021 / DORO 2021（DRO 对 20% 翻转标签极敏感，ERM 几乎不受影响）→ Q2

## C2 · Q1 与 Q4（WebSearch）

**Q1：假设被推翻。** 安全域已有成体系标签噪声感知训练：
- **SLB** Deep Learning from Imperfectly Labeled Malware Data，**CCS 2025**，DOI `10.1145/3719027.3765197`，Zotero `74SZTPTS`（在线摘要）
- **RAPIER** Low-Quality Training Data Only?，**NDSS 2024**，arXiv `2309.04798` / DOI `10.14722/ndss.2024.23081`（**加密恶意流量**，在线摘要）
- **PLCDroid**，**Computer Journal 69(7):1218–1236 (2026)**，DOI `10.1093/comjnl/bxag021`（**pseudo-label noise + concept drift**，十年跨度，FNR 76.0%→47.6%，在线摘要）
- **RoMaC** arXiv `2609.22835`；**LFreeDA** arXiv `2511.14963`；**ALPHA** AsiaCCS'26；**UCF** ACM `10.1145/3803291.3803308`；UCL/SATML 2025 Label Noise in Borderline Samples

**Q4：VT 标签时间不可靠性已被系统测量：**
- **Zhu 等** Measuring and Modeling the Label Dynamics of Online Anti-Malware Engines，**USENIX Sec 2020**（仅题录+二手引述）
- **Re-measuring…from Millions of Samples**，ACM `10.1145/3618257.3624800`，Zotero `3W3WUS2K`（14 个月，**仅 10.9% 达稳定 AV-Rank**）
- **Maat** arXiv `2007.00510`，Zotero `KI4F5PAS`（**含 PDF，全文已落盘**）
- Don't Pick the Cherry arXiv `1903.10560`（2013 良性→2018 复扫 17/60 判恶）；UTEP 学位论文（阈值 13 恶意 −69.89%）
- **反向证据（本地全文）**：LAMDA 结论「**VT 阈值变化影响小**，退化更可能来自时间概念漂移与类不均衡而非 VT 标签噪声」→ **削弱**假设

## C3 · Q3

**《Learning under Temporal Label Noise》**（Nagaraj, Gerych, Tonekaboni, Goldenberg, Ustun, Hartvigsen），**ICLR 2025**，arXiv `2402.04398v2`，Zotero `XH6JKXYY`（**含 PDF，全文已完整读取**）：
- **正式命名并形式化 temporal label noise**；定义 `Q : R⁺→[0,1]^{C×C}`，`Q_t` = `q_t(ỹ_t=j|y_t=i)`
- 前向时间损失 + **Prop. 1**（噪声标签上最小化 = 干净标签上最大化经验似然）；Continuous / Discontinuous / Plug-In 三法
- 4 医疗数据集，30% 噪声；moving/Mixed 测试误差 29.4%（Ignore）→ **4.2%**（Continuous）
- **局限（原文）**：假设所有序列共享同一噪声函数；**假设时序平稳**（`predictive distribution is stable over time`）

其他：**《An Adaptive Method for Weak Supervision with Drifting Data》** arXiv `2306.01658`，Zotero `2FRL6EIQ`（**含 PDF**，弱监督源准确率随时间漂移 + 动态窗口 + 形式化质量保证）；ACM CSUR `10.1145/3494832`；ACM `10.1145/3614419.3644028`；arXiv `2207.04003`；ISPRS label ageing；HAL `tel-05457833`。

## C4 · Q2（方法族与理论底座）

- **损失纠正**：Natarajan NeurIPS 2013（arXiv `1306.1091`）；**Patrini CVPR 2017**（arXiv `1609.03683`，**Thm 1：`T` 非奇异 ⇒ 纠正损失极小点 = 干净分布极小点**）；Ghosh AAAI 2017（arXiv `1703.06476`，对称噪声无需纠正）
- **转移矩阵**：anchor point（Liu & Tao 2015；Patrini 2017）；Xia NeurIPS 2019；**Li ICML 2021** VolMinNet（无 anchor 可证）；Yao NeurIPS 2020 Dual-T；Yong ICLR 2023
- **可辨识性**：**Liu, Cheng, Zhang** arXiv `2202.02016`（三条 i.i.d. 噪声标签为实例级可辨识**充要**条件；Kruskal；`d* ≥ K` 或 `⌈log₂((K+2)/2)⌉`；带隐组 `d* ≥ 2|G|K−1`；**估计误差下界 Thm 8**）；NeurIPS 2022 `98f8c89a…`（Thm 3/4）
- **重加权/再选样**：Liu & Tao TPAMI 2015；Ren ICML 2018；Jiang ICML 2018 MentorNet；Han NeurIPS 2018 co-teaching；Li ICLR 2020 DivideMix；Liu & Guo ICML 2020 Peer loss；SoRR 2021（本地全文）；**DORO 2021 反例（本地全文）**
- **形式化底座**：**Luo, Chen, Zhou, Gong**《A Theoretical Perspective on Streaming Noisy Data With Distribution Shift》，**TPAMI 48(4):4150–4166 (2026)**，DOI `10.1109/TPAMI.2025.3643174`，Zotero `S88SVIZF`——**CNLL 累积泛化误差上界**，三类遗忘来源：缓冲选择偏置/分布漂移/标签噪声

## 事故记录

1. **Zotero 误入库**：未核验 DOI `10.1145/3097983.3097988` → 实为无关的 *Structural Deep Brain Network Mining*，键 **`MD8C7GCM`**。正确 DOI `10.1145/3097983.3098163`（→ `7U6XBRU4`）。`MD8C7GCM` **未清理**（无删除工具）。
2. **WebFetch 全环境无外网**，任务 §三 的 OpenAlex 通路不可用。
3. **Write report 被 harness 拦**，报告改由回复正文承载。

## 新增 Zotero 条目

`7U6XBRU4`（Anderson&McGrew）、`3W3WUS2K`（Re-measuring）、`74SZTPTS`（SLB/CCS'25）、`S88SVIZF`（CNLDD/TPAMI）——均无 PDF；
`2FRL6EIQ`、`XH6JKXYY`（Temporal Label Noise，全文已读）、`KI4F5PAS`——**含 PDF**；
`MD8C7GCM` ⚠️ 误入库。

导入失败（超时/429）：arXiv `2309.04798`、`2202.02016`、`1609.03683`、`1306.1091`、`1703.06476`、`1903.10560`。

## 未关闭疑点

- [ ] SLB / RAPIER / PLCDroid / Zhu 2020 / arXiv 2202.02016 全文未取
- [ ] LAMDA 附录 F 表 13 原文页码未核
- [ ] 「安全域 + 年份函数化标签可靠性」组合是否真空白 —— 需 OpenAlex REST 复核（本会话不可用）
