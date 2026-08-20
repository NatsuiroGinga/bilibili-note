# 第一二章文献建设 — 工作笔记

RESEARCH_ROUTE=RWKV
建立日期：2026-08-19

本文件按「每完成一组查询立即落盘」的规则滚动追加，不等任务结束补写。

---

## 检查点 CP-01（S0–S2 起点）

时间：任务开始。
已完成：
- 读取 `AGENTS.md`（根）、`thesis/AGENTS.md`、`raw/AGENTS.md`、`wiki/AGENTS.md`、
  `.Codex/docs/RWKV/AGENTS.md`、`.Codex/docs/RWKV/2026-08-19-第一二章骨架与写作规范.md`。
- 建立本任务目录与 `task_plan.md`。

实测命令与结果：

```
fd -e pdf . raw/papers/ | wc -l      → 446
fd -e md  . wiki/papers/ | wc -l     → 507
```

`raw/papers/` 目录级 PDF 计数（非递归，命令见下）：

```
for d in $(fd -t d . raw/papers/ | sort); do n=$(fd -e pdf . "$d" --max-depth 1 | wc -l); echo "$n $d"; done
```

| 目录 | 篇数 |
| --- | ---: |
| `attack-detection/` | 37 |
| `attack-detection/drift/` | 2 |
| `attack-detection/early-detection/` | 1 |
| `attack-detection/encrypted/` | 13 |
| `attack-detection/entity-granularity/` | 4 |
| `attack-detection/open-set/` | 1 |
| `cdn-ops/` | 6 |
| `datasets/` | 9 |
| `datasets/LSPR24/` | 3 |
| `datasets/analog-benchmarks/` | 3 |
| `datasets/citation-only/` | 1 |
| `datasets/data-protocol/` | 8 |
| `datasets/locked-shields-related/` | 2 |
| `datasets/published-baseline/` | 7 |
| `datasets/quic/` | 12 |
| `datasets/quic/citing/` | 4 |
| `datasets/quic/task-landscape/` | 9 |
| `deepseek/` | 2 |
| `game/` | 24 |
| `grpo/` | 17 |
| `llm/` | 1 |
| `manifold/` | 15 |
| `methodology/` | 75 |
| `methodology/multiple-instance/` | 15 |
| `methodology/ranking/` | 5 |
| `methodology/soc-alert-operations/` | 2 |
| `pinn/` | 45 |
| `pinn/multiscale-observability-closure/` | 20 |
| `pinn/network-calculus-boundary/` | 17 |
| `pinn/pcap/` | 17 |
| `pinn/protocol-adaptive/` | 20 |
| `proceedings/` | 1 |
| `rwkv/` | 34 |
| `traffic-foundation-models/` | 11 |
| `raw/papers/` 根散落 | 3 |
| **合计** | **446** |

待办：目录名不足以判轴（尤其 `methodology/` 75 篇、`pinn/` 各子目录、`attack-detection/` 37 篇），
须按文件名逐条粗分并抽查。

---
## 检查点 CP-02（S4 原件↔笔记对应关系，实测）

时间：盘点第 2 段。执行者：Claude Opus 5 子代理（本轮）。

脚本（一次性，写在 scratchpad，未入仓）：遍历 `raw/papers/**/*.pdf` 与 `wiki/papers/**/*.md`，
解析笔记 YAML 前言的 `source_pdf` 字段，按**文件基名**匹配。

实测结果：

| 项 | 数 |
| --- | ---: |
| `raw/papers/` PDF 总数 | 446 |
| 有 `wiki/papers/` 笔记指向的 PDF | **416** |
| 无任何笔记指向的 PDF | **30** |
| `wiki/papers/` `.md` 总数 | 507 |
| 其中无 `source_pdf` 字段（`INDEX.md` 与两篇专题笔记） | 16 |
| 论文笔记数（507 − 16） | **491** |
| `source_pdf` 唯一取值数 | 438 |
| **`source_pdf` 指向不存在原件的笔记（"有笔记无原件"）** | **0** |

推论（非实测）：491 篇论文笔记覆盖 416 个不同原件，说明约 75 篇是同一原件的第二篇笔记
（多轮阅读或不同角度）；`source_pdf` 唯一取值 438 > 覆盖原件 416，差额来自同一原件
被写成 `[[文件名.pdf]]` 与 `[[raw/papers/…/文件名.pdf]]` 两种形态。**该形态不统一是既存缺陷，本轮只记录不修改。**

**结论：本仓库不存在「笔记但无原件」的情况（0 篇）。** 用户简报中该问项的答案为零。

### 30 篇无笔记 PDF（证据等级 B，须补笔记后才可定稿）

按目录分布：`methodology/` 19 篇（占 63%）、`attack-detection/` 2、`pinn/` 3、`rwkv/` 2、
`datasets/quic/` 1、`proceedings/` 1、`methodology/multiple-instance/` 1、根散落 1。

其中 3 篇属重复件或非论文，不需补笔记：
- `raw/papers/1-s2.0-S2352340925002197-main (2).pdf`（同名重复件）
- `raw/papers/attack-detection/2026-Kim-CANDI-Curated-TTA-arXiv-v1.pdf`（同论文 v1，已有终稿笔记）
- `raw/papers/attack-detection/encrypted/2019-Kanzig-ML-Detection-CC-Channels-CyCon-SLIDES.pdf`（幻灯片，非论文）
- `raw/papers/datasets/quic/H23Q-…-arXiv2208.06722-verified.pdf`（同论文核验副本）
- `raw/papers/proceedings/2025-ARES-LNCS15993-Proceedings-Part-II.pdf`（会议论文集整卷）
- `raw/papers/methodology/2018-Lipton-BBSE-Label-Shift-Supplement.pdf` 与
  `raw/papers/methodology/2024-Hu-EnsV-…-Supplement.pdf`（补充材料，正文已有笔记）

**实际须补笔记的独立论文：22 篇**，清单见交付文件。

待办：判定这 22 篇分属哪条轴；其中标签移位族（Lipton BBSE 正文已有笔记，
Alexandari MLLS、Garg 统一视角、Azizzadenesheli RLLS、Scott 广义 NP）**全部落在轴二**，是本轮最大的单点缺口。


---
## 检查点 CP-03（S2–S3 分轴分类，实测）

分类脚本与最终标签落盘：`原件分轴清单.tsv`（446 行 + 表头），字段
`轴 / 笔记深度 / 原件路径 / 笔记题名`。分类先按目录规则，再按文件名关键词，
最后对 18 个存疑项读取 `wiki/papers/` 笔记的 `title` 字段核对后手工改判。

手工改判（有据）：
- `rwkv/2026_Sharma_PLM-NIDS…` 与 `rwkv/2026_Kulatilleke_MambaNetBurst…` 由 C 改 A
  （题名分别为「基于 RWKV 协议语言模型的无深度包检测网络入侵检测」与
  「Direct Byte-level Network Traffic Classification without Tokenization」，属表示层演进）。
- 由 C 改 D 共 13 项：AgentDojo（提示注入评估）、Multigrain 全色锐化、WKV-Sharing 全色锐化、
  PointRWKV、Vision-RWKV、`electricity-07-00058`（电力负荷）、`engproc-97-00026`（电力负荷）、
  `Monthly_Service_Prediction`（4G/5G 业务量）、`S0360544224028433`（光伏功率）、
  `2026_Ilic`（语言模型记忆签名）、`SAM-Decoding`（推测解码）、RADLADS（注意力蒸馏）、
  Quantum-Enhanced RWKV。这些是骨干跨域可迁移性证据，**不能进 1.2 综述**。
- `proceedings/2025-ARES-LNCS15993-Proceedings-Part-II.pdf` 单列为 `X`：整卷会议论文集，
  不是可引条目。
- `attack-detection/朱焱雷.pdf` 单列为 `REF`：对标学位论文，只作结构参照。

最终分轴计数（实测，合计 446）：

| 轴 | 篇数 | 深笔记 | 浅笔记 | 无笔记 |
| --- | ---: | ---: | ---: | ---: |
| A 表示与判定方法演进 | 95 | 56 | 25 | 14 |
| B 跨年度漂移与实体级判定 | 99 | 40 | 20 | 39 |
| C 双时域证据与预算标定（储备） | 36 | 22 | 4 | 10 |
| D 与当前路线无关 | 214 | — | — | — |
| X 非条目（整卷论文集） | 1 | 0 | 0 | 1 |
| REF 对标学位论文 | 1 | 1 | 0 | 0 |

「深笔记」判据（可复算）：笔记正文 ≥ 2200 字符**且**出现 ≥ 3 处
`第N页 / p.N / 表N / 图N / Section N / §N / 式(N)` 定位标记。
该判据是**全文核验的必要条件而非充分条件**；本轮未逐篇回原件复核，
故所有「深笔记」条目只登记为 **待核验候选**，不得当作已核验条目使用。

待办：逐轴子话题缺口定位；前序 E1–E25 / N1–N8 复用判定；联网补充清单。

---
## 检查点 CP-04（S6 前序成果复用，实测）

来源：`.Codex/docs/2026-08-18-实体粒度部署证据调研/候选证据清单.md`（531 行）。
命令：`rg -n '^### [EN][0-9]+' <file>` 得 E1–E25 与 N1–N8 共 33 条；
`rg -o 'raw/papers/\S+'` 去重得 **19 个不同原件**（33 条条目里存在一稿多用，
如 Ho Hopper 同时是 E6/E11/E23，Zhang ACSAC 同时是 E9/E17/E24/N2，
Dijk 2026 同时是 E25/N3/N4）。

其自报证据等级分布：A 级 13 条、B 级（预印本或学位论文）7 条、C 级（仅线索）1 条。

其「待关闭事项」三项，本轮原样继承，不得视为已关闭：
1. 题录待核：Pevný & Somol 正式会议与页码、Yen 2013 与 Bilge 2012 的 ACSAC 页码、
   Cui 2023 CBSeq 正式期刊出处。
2. 原件待补（付费墙／反爬）：Axelsson 2000 TISSEC、Clausen 2021 CBAM 正式版、
   Apruzzese 2017 NCA、Hassan 2019 NoDoze。
3. 反面证据偏弱：N1 出自预印本。

待办：联网补充清单成文。

---
## 检查点 CP-05（S5/S7，缺口与联网清单）

中文文献实测：`rg -o 'journal:\s*"?…学报|计算机|通信…'` 于 `wiki/papers/`，
与本课题轴 A／轴 B 相关的中文载体笔记 **0 篇**
（唯三命中为郑州大学学报的用户异常检测、《电子通信与计算机科学》的视频 CDN、
《计算机科学》的 PINN 综述，前两者不属 A/B，第三者属 D）。
**这是本轮发现的最大结构性缺口**：中文学位论文 1.2 通常需要中文文献支撑，本地储备为零。

本轮**未联网**，故所有「本地未收录」判断一律表述为「本地未检索到」，
不表述为「不存在」。联网补充清单见最终交付。
## 检查点 CP-03（S2–S3 四轴分类完成，实测）

分类方法：以 `raw/papers/` 目录归属为一级规则，文件名与笔记 `title` 关键词为二级规则，
再对 23 篇目录归属与实际主题不符者做逐条覆盖（`FORCE4` 与 `NONCITE` 名单，写在一次性脚本内）。
分类脚本与四份轴清单在 scratchpad，未入仓；清单已复制进本轮交付文件。

### 分类结果（合计 446，无遗漏无重复）

| 类 | 篇数 | 有笔记 | 无笔记 | 笔记 ≥1500 字符 |
| --- | ---: | ---: | ---: | ---: |
| 非条目（重复件／幻灯片／补充材料／论文集整卷／非论文） | 9 | 1 | 8 | 0 |
| 轴一 领域总体 | **89** | 86 | 3 | 76 |
| 轴二 跨年度漂移与实体级判定 | **89** | 76 | 13 | 50 |
| 轴三 第四章方向储备 | **15** | 15 | 0 | 8 |
| 轴四 与当前路线无关 | **244** | 238 | 6 | 91 |

**轴四占 54.7%**，与「第一二章旧引文整个作废」的判断一致：
`pinn/` 119 篇、`game/` 24、`grpo/` 17、`manifold/` 15、`cdn-ops/` 6、`deepseek/` 2、`llm/` 1
合计 184 篇纯历史路线；另有 23 篇散落在 `attack-detection/`、`methodology/`、`rwkv/`、
`datasets/quic/` 但主题属历史路线（GRPO、LoRA、约束策略优化、QUIC 协议机制、RWKV 非检测应用）。

### 归类覆盖名单（目录与主题不符，人工改判）

改判入轴四 14 篇：`methodology/` 的 Achiam 约束策略优化、Polosky 约束离线策略优化、
Cotter 两人博弈约束优化、Cotter 约束泛化、Hu SAM 后缀自动机解码；
`attack-detection/` 的 `2211.10833`、`2602.00513`、`2604.03790`、`2605.29317`、`2601.04443`、
`2411.10918`、TCP-AQM 混沌控制；`rwkv/` 的 AgentDojo 提示注入、自回归语言模型记忆签名。
`datasets/quic/` 另有 12 篇属 QUIC 协议机制（互操作测试、spin bit、拥塞控制、能耗、
中间盒、握手、隐写、连接迁移），非检测方法演进，一并入轴四。

判为非条目 9 篇：`1-s2.0-S2352340925002197-main (2).pdf`（重复件）、
`2026-Kim-CANDI-Curated-TTA-arXiv-v1.pdf`（同论文旧版）、
`2019-Kanzig-…-CyCon-SLIDES.pdf`（幻灯片）、
`H23Q-…-arXiv2208.06722-verified.pdf`（核验副本）、
`2018-Lipton-BBSE-…-Supplement.pdf`、`2024-Hu-EnsV-…-Supplement.pdf`、
`2021-Schlag-…-DeltaNet-supplement.pdf`（三份补充材料，正文均已单独在库）、
`2025-ARES-LNCS15993-Proceedings-Part-II.pdf`（论文集整卷）、
`Obsidian-AI-v1.0.0.pdf`（非论文）。

**待办**：轴一与轴二须按子话题细分，判定 15–20 条密度能否满足。

---

## 检查点 CP-04（题录质量红线，实测，**本轮最重要发现**）

查询：对 446 篇的笔记 YAML 前言逐条解析 `year` 与 `journal`，检查取值是否可信。

实测：

- **`year` 字段取值落在 1950–2030 之外的笔记：34 篇。** 多数是 Unix 时间戳被误写入，
  例：`raw/papers/attack-detection/2411.10918.pdf` 的 `year: 1784021866.3411586`；
  另有 `year: 2056`、`year: 2099`、`year: 2036`、`year: 1952`、`year: 1953`、`year: 1985` 等。
- **`journal` 字段明显张冠李戴：17 篇。** 例：
  - `attack-detection/2211.10833.pdf` → `The American Mathematical Monthly`
  - `grpo/2402.03300.pdf`（DeepSeekMath）→ `International Journal of Radiation Oncology*Biology*Physics`
  - `grpo/2601.22478.pdf` → `The IUPAC Compendium of Chemical Terminology`
  - `cdn-ops/2401.15839v1.pdf` → `Medicine & Science in Sports & Exercise`
  - `manifold/PITT-2305.08757.pdf` → `Ultrasound in Medicine & Biology`

**结论（硬约束）：`wiki/papers/` 的 YAML 前言不能作为题录来源。**
第一二章任何一条引注的作者、年份、载体、卷期页码都必须回 `raw/papers/` 原件首页
或出版社正式题录核出。这条与用户简报「不得凭记忆写题录」同向，但把风险从「代理记忆」
扩大到「本仓库既有笔记元数据」，范围更大。

**风险边界（实测）**：34 篇坏 `year` 与 17 篇坏 `journal` **全部落在轴四**
（`grpo/` 15、`manifold/` 6、`game/` 4、`attack-detection/` 历史路线误置 8、
`deepseek/` 2、`llm/` 1、`cdn-ops/` 1）。**轴一、轴二、轴三的笔记题录未命中该组坏值。**
但未命中不等于已核验——轴一二三仍须逐条回原件核对，本轮不作任何题录定稿。

**本轮不修复这些坏题录**（属 `wiki/` 写入，超出本任务范围，且用户约束为盘点）。
建议主代理另开任务清理，或在第一二章定稿时对实际引用到的条目逐条覆盖修正。

## 检查点 CP-05（S6 前序成果复用逐条判定）

来源：`.Codex/docs/2026-08-18-实体粒度部署证据调研/候选证据清单.md`（531 行，已完整读取）。
交叉核对：`.Codex/docs/RWKV/2026-08-19-第三章引注核验报告.md`（241 行，已完整读取）。

`E1`–`E25` 与 `N1`–`N8` 共 33 个编号，但**多个编号指向同一篇原件**
（E6=E11=E23 同为 Ho Hopper；E9=E17=E24=N2 同为 Zhang ACSAC 2023；
E2=E10=E18 同为 Bilge；E4=E16 同为 Hu；E15=N1 同为 Garcia & Valeros；
E25=N3=N4 同为 Dijk SSRN；E14=N6 同为 Li Sensors；E20=N5 同为 Anderson）。
**去重后为 20 篇不同来源。**

其中 3 篇**已占用第三章编号，不可重复编号**：
- Gehri 2023 CyCon（E22）= 第三章 `[1]`／`[3]`（`[3]` 将并入 `[1]`）
- Lee & Stolfo 2000 TISSEC（E19）= 第三章 `[10]`（已成文）
- Dijk SSRN 6597680（E25）= 第三章 `[2]`

**可从 `[11]` 起新编的 = 17 篇**，其中 16 篇本机有原件、1 篇仅网页无原件。

### 逐条判定（去重后）

| # | 来源 | 原件 | 前序等级 | 进轴 | 判定 |
| --- | --- | --- | --- | --- | --- |
| 1 | Pevný & Somol 树结构多示例 | `methodology/multiple-instance/2016-Pevny-Discriminative-Models-Tree-Structure-MIL-AISec.pdf` | A（内容），题录待核 | 轴二 | **可用**，正式会议与页码须先核定 |
| 2 | Bilge et al. DISCLOSURE ACSAC'12 | `…/2012-Bilge-DISCLOSURE-Botnet-C2-NetFlow-ACSAC.pdf` | A | 轴二 | **可用**，ACSAC 页码待补 |
| 3 | Yen et al. Beehive ACSAC'13 | `…/2013-Yen-Beehive-Enterprise-Log-Analysis-ACSAC.pdf` | A | 轴二 | **可用**，ACSAC 页码待补 |
| 4 | Hu et al. BAYWATCH DSN 2016 pp.479–490 | `attack-detection/encrypted/2016-Hu-BAYWATCH-Beaconing-Detection-DSN.pdf` | A，题录完整 | 轴二＋轴三 | **可直接用** |
| 5 | Cui et al. CBSeq | `attack-detection/encrypted/2023-Cui-CBSeq-Encrypted-Malware.pdf` | B（预印本） | 轴一＋轴二 | 可用但须标预印本；正式期刊出处待核 |
| 6 | Ho et al. Hopper USENIX Sec 21 pp.3093–3110 | `methodology/soc-alert-operations/2021-Ho-Hopper-Lateral-Movement-USENIXSec.pdf` | A，题录完整 | 轴二 | **可直接用** |
| 7 | Dainotti et al. IEEE Network 26(1):35–40 | `attack-detection/entity-granularity/2012-Dainotti-…-IEEE-Network.pdf` | A，题录完整含 DOI | 轴二 | **可直接用** |
| 8 | Alahmadi et al. USENIX Sec 22 pp.2783–2800 | `methodology/soc-alert-operations/2022-Alahmadi-…-USENIXSec.pdf` | A，题录完整 | 轴二 | **可直接用** |
| 9 | Zhang et al. ACSAC 2023 聚合信标 | `attack-detection/encrypted/2023-Zhang-Aggregation-Beaconing-Detection-ACSAC.pdf` | A | 轴二＋轴三 | **可用**，ACSAC 页码待补 |
| 10 | Sun et al. 在线自适应异常阈值 | `methodology/2024-Sun-Online-Adaptive-Anomaly-Thresholding.pdf` | A（内容） | 轴三 | 可用，正式出处待核（本机为 ICML 系列版式） |
| 11 | Arp et al. USENIX Sec 2022 | `datasets/data-protocol/2022-Arp-Dos-and-Donts-ML-Computer-Security.pdf` | A | 轴一（评价方法学） | **可用**，页码待补 |
| 12 | Li et al. Sensors 2024, 24(7):2122 | `attack-detection/entity-granularity/2024-Li-…-Sensors.pdf` | A，题录完整含 DOI | 轴二 | **可直接用** |
| 13 | Garcia & Valeros arXiv:2305.01337 | `attack-detection/entity-granularity/2023-Garcia-…-arXiv2305.01337.pdf` | B（预印本） | 轴二 | 可用但须标预印本 |
| 14 | Anderson & McGrew AISec'16 pp.35–46 | `attack-detection/encrypted/2016-Anderson-…-Contextual-Flow.pdf` | A，题录完整含 DOI | 轴一＋轴二 | **可直接用** |
| 15 | El Mahdaouy et al. arXiv:2602.05594 综述 | `methodology/multiple-instance/2026-Contextualized-NetFlow-DL-NIDS-Survey.pdf`（另有同文副本） | B（预印本） | 轴一＋轴二 | 可用但须标预印本；**本机该副本无笔记** |
| 16 | Leoste 硕士论文 TalTech 2025 | `datasets/LSPR24/2025_Leoste_…_LSPR23_LSPR24.pdf` | B（学位论文） | 轴二 | 可用但须标学位论文 |
| 17 | DistriNet CSE-CIC-IDS2018 重标注网页 | **无原件** | C（网页） | — | **不得进正文**；须先取得 CNS 2022 论文原件 |

**汇总：可直接进轴二／轴一的 A 级 = 11 篇**（第 1–4、6–9、11、12、14 项中的 A 级者），
**须标注证据等级的 B 级 = 4 篇**（Cui、Garcia、El Mahdaouy、Leoste），
**不可用 = 1 篇**（DistriNet 网页）。
另 1 篇（Sun）为 A 级内容但正式出处待核，落轴三不落本轮定稿范围。

**题录待补清单（前序文件第七节已列，本轮确认仍未关闭）**：
Pevný & Somol 正式会议与页码；Yen 2013 与 Bilge 2012 的 ACSAC 页码；
Cui 2023 CBSeq 正式期刊出处；Zhang 2023 ACSAC 页码；Arp 2022 USENIX 页码；
Sun 在线阈值论文的正式出处。**这 6 项都需要联网查出版社页，本机 PDF 文本层无。**

## 检查点 CP-06（原件完整性全量扫描，实测）

命令：对 `all_pdfs.txt` 中 446 条逐条执行 `pdfinfo "$f" >/dev/null 2>&1`，非零退出即判损坏。

**10 篇原件损坏**（`Invalid XRef entry 0` / `Couldn't find trailer dictionary`）：

| 原件 | 轴 | 是否有笔记 | 影响 |
| --- | --- | --- | --- |
| `methodology/2019-Azizzadenesheli-RLLS.pdf` | 轴二 | 无 | **须重下**，标签移位族 |
| `methodology/2020-Garg-Unified-Label-Shift.pdf` | 轴二 | 无 | **须重下**，标签移位族（第三章报告已提及） |
| `methodology/2007-van-der-Laan-Super-Learner.pdf` | 轴一 | 无 | 须重下或判为不需要 |
| `methodology/2010-Polley-Super-Learner-Dissertation.pdf` | 轴一 | 无 | 同上 |
| `datasets/quic/citing/2022-Chaudhary-…-Middleboxes.pdf` | 轴四 | 有 | 不影响第一二章 |
| `datasets/quic/citing/2023-Caiazza-…-PMC.pdf` | 轴四 | 有 | 同上 |
| `datasets/quic/citing/2024-Muecke-ReACKed-QUICer-…-IMC.pdf` | 轴四 | 有 | 同上 |
| `grpo/2511.03527.pdf`、`grpo/2512.15347.pdf`、`grpo/2601.22478.pdf` | 轴四 | 有 | 同上 |

**注意第五、六、七行的矛盾**：三篇 QUIC citing 与三篇 grpo 原件已损坏却存在笔记，
说明这些笔记要么写于损坏之前，要么并非基于本机原件全文。**不作为可信全文证据。**

---

## 检查点 CP-07（轴一叙事缺口探针，实测）

方法：对 1.2.1「表示与判定方法演进」叙事所需的经典工作逐个探针，
命令形如 `fd -e pdf . raw/papers/ -i | rg -ic "<关键词>"` 与 `rg -ilc "<关键词>" wiki/papers/`。

| 探针 | 原件文件名命中 | 笔记命中 | 判定 |
| --- | ---: | ---: | --- |
| Lotfollahi / Deep Packet | 0 | 0 | **缺** |
| Draper-Gil / ISCX VPN-nonVPN | 0 | 18（仅被他文引用） | **原件缺** |
| Velan / Papadogiannaki / Rezaei / Aceto（加密流量分类综述） | 0 | ≤1 | **全缺，本库无任何一篇加密流量分类领域综述** |
| Taylor AppScanner | 0 | 3（被引） | **原件缺** |
| Panchenko / Rimmer / Sirinam（网站指纹经典） | 0 | 0 | **缺**（仅有 QUIC 时代三篇） |
| Korczyński / Husák（TLS 指纹） | 0 | 0 | **缺**（仅有 JA4+ 一篇 2024） |
| Dyer / Wright（加密流量分析经典） | 0 | 0 | **缺** |
| Sommer & Paxson《Outside the Closed World》S&P 2010 | 0 | 1（被引） | **原件缺** |
| Axelsson 基率谬误 TISSEC 2000 | 0 | 1（被引） | **原件缺**（前序任务已列阻塞） |
| MIMETIC / DISTILLER（Aceto 多模态） | 0 | 0 | **缺** |
| 笔记 `title` 含 survey/review/综述 者 | — | 7，**其中 6 篇是 PINN 综述，1 篇是靶场技术综述** | **本库无当前主线的领域综述** |

**结论：轴一的缺口不是"篇数不够"，而是"叙事的前半段整段缺失"。**
本库 89 篇轴一材料压倒性集中在 2022–2026 的深度学习、预训练与线性骨干段
（`traffic-foundation-models/` 11 + `rwkv/` 骨干 13 = 24 篇），
而端口与深度包检测时代、统计特征加经典机器学习时代、网站指纹与 TLS 指纹时代
几乎无原件，领域综述为零。

---

## 检查点 CP-08（轴二子话题缺口探针，实测）

| 探针 | 原件 | 笔记 | 判定 |
| --- | ---: | ---: | --- |
| Transcend（Jordaney USENIX Sec 17，漂移拒识） | 0 | 1（被引） | **原件缺** |
| CADE（Yang USENIX Sec 21，漂移样本解释） | 0 | 3（被引） | **原件缺** |
| INSOMNIA / Andresini（NIDS 概念漂移） | 0 | 1 | **原件缺** |
| Barbero / Ceschin / Kantchelian（安全领域漂移） | 0 | ≤1 | **缺** |
| Radenović & Tolias & Chum GeM TPAMI 2018 | 0 | 0 | **缺**，第三章 `[9]` 阻断项 B4 的同一篇 |

**轴二总体判定：储备充足，但漂移子话题的安全领域经典缺原件。**
本库轴二 89 篇里 41 篇在 `methodology/`（通用域适应、标签移位、模型选择的机器学习方法论），
只有 2 篇在 `attack-detection/drift/`。也就是说，
**"分布漂移的方法论"很厚，"安全与入侵检测领域自己的漂移工作"很薄。**
1.2.2 若照对标论文「每段绑定一个流派、每项工作一句」的写法，
用通用机器学习漂移文献撑满一节会偏离「加密恶意流量检测」这一学科归属。


---

## 检查点 CP-09（定稿阶段题录回原件复核，2026-08-19，实测）

执行者：第一二章文献建设定稿代理。方法：对拟定稿条目逐条 `pdftotext -layout` 读首页与末页页眉页脚，
只采信原件文本层可见的载体、卷、期、页码与 DOI。命令形如：
`pdftotext -layout -f 1 -l 1 <原件> - | rg -v '^\s*$' | head/tail`。

### 存在性核验（全通过）

- 67 条拟用原件路径逐条 `test -f`，缺失 0。
- 67 条原件按 basename 反查 `wiki/papers/`，仅 1 条无笔记：
  `raw/papers/methodology/multiple-instance/2026-Contextualized-NetFlow-DL-NIDS-Survey.pdf`（E21），与轴A/轴B交付一致。

### 本轮新关闭的题录待补项（7 项，均由原件读出，非联网）

| 条目 | 上游状态 | 本轮实测 | 证据位置 |
| --- | --- | --- | --- |
| Ben-David 域适应不可能性 | 卷内页码未印 | JMLR W&CP 9: 129-136 | p.1 页脚 129；p.8 页脚 136 |
| Zhang 聚合信标检测 ACSAC 2023 | 页码待补 | pp. 565-579，DOI 10.1145/3627106.3627126 | p.1 页脚 565 与 DOI；p.15 页脚 579 |
| Jacobs CCS 2022 | 页码未核 | pp. 1537-1551 | p.1 页脚 1537；p.15 页脚 1551 |
| Clausen CBAM | 卷期文章号待补 | Computers 2021, 10(6): 79，DOI 10.3390/computers10060079 | p.1 MDPI Citation 块与页脚 |
| Kim TTA-AD AAAI-24 | 页码待补 | pp. 13113-13121 | p.1 页脚 13113；p.9 页脚 13121 |
| Hu BAYWATCH DSN 2016 | 仅起页已核 | pp. 479-490，DOI 10.1109/DSN.2016.50 | p.1 页脚 479 与 DOI；p.12 页脚 490 |
| Li Sensors 2024 | 卷期文章号未复核 | Sensors 2024, 24(7): 2122，DOI 10.3390/s24072122 | p.1 Citation 块与页脚 |

另复核确认（与上游一致）：Jordaney TRANSCEND pp. 625-642（PDF p.1 为 USENIX 封面页无页码，p.2=625，p.20 页脚 642）；
Bartos pp. 807-822；Yang CADE pp. 2327-2344；Ho Hopper pp. 3093-3110；Alahmadi pp. 2783-2800；
Anderson AISec'16 pp. 35-46 与 DOI 10.1145/2996758.2996768；Dainotti IEEE Network 2012 年 1/2 月号 pp. 35-40；
Ganin JMLR 17 (2016) 1-35；Malekghaini Computer Networks 225 (2023) 109648；Dijk LSPR23 JISA 85 (2024) 103847；
陈子涵《计算机学报》第 46 卷第 5 期，p.1=1060，p.26=1085；ET-BERT DOI 10.1145/3485447.3512217。

### 本轮纠正的一处上游表述

轴A交付称 TrafficFormer「原件正文出现 2025 IEEE Symposium on Security and Privacy 程序委员会字样」。
实测：全文 `Symposium on Security and Privacy` 三处命中，其中一处在参考文献表内（第 2444 行），
另两处在 Appendix A Meta-Review 抬头（第 2506-2507 行）：
「prepared by the program committee for the 2025 IEEE Symposium on Security and Privacy (S&P)」。
**结论：载体为 IEEE S&P 2025 成立，但依据是附录 A 的元评审抬头，不是首页载体标注；页码与 DOI 原件不含，仍待补。**

### 本轮确认仍不可从原件闭合的题录（不得凭记忆填）

Moore & Zuev（SIGMETRICS'05 作者版无页码）、Karagiannis BLINC（SIGCOMM'05 作者版无页码）、
Sommer & Paxson（ICSI 作者版无页码）、Rezaei & Liu（原件页眉为 SUBMITTED TO IEEE COMMUNICATIONS MAGAZINE，即预印本）、
Arp（原件为 arXiv:2010.09470v2，无 USENIX 页码）、Flood（无会议页眉）、Känzig（卷名与编者已核，页码未印）、
Bilge ACSAC'12 与 Yen ACSAC'13（两者首页只有 ACM 版权块与 ISBN，无卷内页码）、
INSOMNIA（camera-ready 未印页码，DOI 10.1145/3474369.3486864 已核）、
Lo E-GraphSAGE（首页脚注为 author's copy，NOMS 2022 已核，页码未印）、
Zhu MIDAM（PMLR 202, 2023 已核，页码未印）、Alexandari（PMLR 119, 2020 已核，页码未印）、
Lipton（PMLR 80，页码未印，第三章已记）、Ilse（PMLR 80，页码未印，第三章已记）。

### 本轮判定不得定稿的条目

Prasse 等 2017：首页为 Springer 单栏版式，**既无载体标注也无 arXiv 标识符**，
无法按正式版著录，也无法按预印本著录（无稳定标识符）。列入未定稿单列。

本检查点未联网、未修改 `thesis/`、`raw/`、`wiki/` 任何文件、未启动 GPU 或远程命令。

---

## 检查点 CP-10（结论汇总代理，2026-08-19）

执行者：结论汇总代理（Claude Opus 5）。范围：把轴 A 与轴 B 的核验结果汇成
`.Codex/docs/RWKV/2026-08-19-第一二章文献建设结论.md`。未修改 `thesis/`、`raw/`、`wiki/`。未联网。未启动 GPU 或远程命令。

### 本检查点自行复核（非转述上游）

| 复核项 | 命令 | 实测 |
| --- | --- | --- |
| 本轮新增 5 篇轴 A 原件存在 | `ls raw/papers/traffic-classification-evolution/` | 5 个 PDF 均在，时间戳 08-19 11:56–11:57 |
| 本轮新增 4 篇漂移族原件存在 | `ls raw/papers/attack-detection/drift/` | 6 个 PDF（含既有 TESSERACT、Malekghaini） |
| 中文综述原件存在 | `ls raw/papers/attack-detection/chinese-surveys/` | 1 个 PDF |
| 陈子涵题录 | `pdftotext -f 1 -l 1` | 首页印「第 46 卷 第 5 期 … 2023 年 5 月」，与 46(5) 一致 |
| TRANSCEND 起页 | `pdftotext -f 2 -l 2` 页脚 | `26th USENIX Security Symposium 625` |
| Bartos 起页 | `pdftotext -f 2 -l 2` 页脚 | `25th USENIX Security Symposium 807` |
| Anderson AISec'16 | `pdftotext -f 1 -l 1` | `AISec'16, October 28 2016, Vienna` + DOI `10.1145/2996758.2996768` + 页脚 `35` |
| Hu BAYWATCH | `pdftotext -f 1 -l 1` 页脚 | 页脚 `479` 且同页印 `DOI 10.1109/DSN.2016.50` |
| Ho Hopper 起页 | `pdftotext -f 2 -l 2` 页脚 | `30th USENIX Security Symposium 3093` |
| Alahmadi 起页 | `pdftotext -f 2 -l 2` 页脚 | `31st USENIX Security Symposium 2783` |
| Ganin 载体 | `pdftotext -f 1 -l 1` 页眉 | `Journal of Machine Learning Research 17 (2016) 1-35` |
| Malekghaini 载体 | `pdftotext -f 1 -l 1` | `Computer Networks 225 (2023) 109648` + DOI |
| 55 条拟用原件的 wiki 笔记 | `rg -l --fixed-strings <basename> wiki/papers/` | 全部命中，无笔记者 0 |

### 本检查点新查出的第二章缺口探针（`fd`，本机零命中）

`radenovic|gem|power.mean|hardy|inequal|quinonero|moreno-torres|dataset.shift|davis.*goadrich|saerens`
在 `raw/papers/` 下仅命中 `2019-Revaud-AP-GeM-ICCV.pdf`、`2023-Yao-GeM-SmoothAP-IET.pdf`、
`2019-Ovadia-Uncertainty-Dataset-Shift.pdf`。即：
Radenović GeM 原始出处、Saerens 2002、Davis & Goadrich 2006、幂平均不等式的数学出处**本机全缺**。

### 编号裁决

新号 `[11]`–`[58]` 共 48 条，复用 `[1][2][4][5][7][8][10]` 共 7 条，1.2 全节合计 55 条不同条目。
Prasse 2017 按 notes.md 上一检查点的裁定排除，不占号。

### CP-10 补充（作者串回原件核出，5 条）

初稿一度对 `[27] [31] [47] [53] [54]` 写了推测作者串，随即回原件 `pdftotext -f 1 -l 1` 逐条核出并覆盖：

| 条目 | 实测作者串 | 出处 |
| --- | --- | --- |
| `[27]` Zhang ACSAC'23 | Yizhe Zhang, Hongying Dong, Alastair Nottingham, Molly Buchanan, Donald E. Brown, Yixin Sun（均 University of Virginia） | 原件 p.1 作者块 |
| `[31]` Jacobs CCS'22 | Arthur S. Jacobs, Roman Beltiukov, Walter Willinger, Ronaldo A. Ferreira, Arpit Gupta, Lisandro Z. Granville | 原件 p.1 作者块与 ACM Reference Format |
| `[47]` Han OWAD NDSS'23 | 12 位，首三位 Dongqi Han, Zhiliang Wang, Wenqi Chen | 原件 p.1 作者行 |
| `[53]` Yen Beehive ACSAC'13 | Ting-Fang Yen, Alina Oprea, Kaan Onarlioglu, Todd Leetham, William Robertson, Ari Juels, Engin Kirda | 原件 p.1 作者块 |
| `[54]` Hu BAYWATCH DSN'16 | Xin Hu, Jiyong Jang, Marc Ph. Stoecklin, Ting Wang, Douglas L. Schales, Dhilung Kirat, Josyula R. Rao | 原件 p.1 作者行；同页页眉印会议全称 |

**教训**：与仓库既有两起同型事故同源——凭记忆写题录（含作者串）不可靠，写入前必须回原件。
本次在同一轮内自查并关闭，未流出到交付文件的最终版本。
