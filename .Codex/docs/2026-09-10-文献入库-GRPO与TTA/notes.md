# 文献入库：GRPO 家族与 TTA 家族（可恢复检查点）

- 任务目录：`.Codex/docs/2026-09-10-文献入库-GRPO与TTA/`
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`（分支 `exp/ch3-drift-20260908`）
- 开始时间：2026-09-10 15:05 左右
- 任务来源：主代理派发（任务 A：GRPO 家族 4 篇；任务 B：TTA 家族 4 篇）

## 一、题录核验（arXiv API，2026-09-10 15:06–15:08）

用 `https://export.arxiv.org/api/query?id_list=...` 逐条核验，**发现两处编号与任务书不符**：

| 目标论文 | 任务书给出的编号 | 实测核验结果 | 处置 |
|---|---|---|---|
| DeepSeekMath（GRPO 原文） | 2402.03300 | **相符**：DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models，Zhihong Shao 等 11 人，published 2024-02-05 / updated 2024-04-27（v3） | 采用 |
| DAPO | 2503.14476 | **相符**：DAPO: An Open-Source LLM Reinforcement Learning System at Scale，Qiying Yu 等 35 人（ByteDance Seed／清华 AIR／HKU），2025-03-18 / updated 2025-05-20（v2） | 采用 |
| Dr. GRPO | 2503.20796 | **不符**：2503.20796 实为 *EXPLICATE: Enhancing Phishing Detection through Explainable AI and LLM-Powered Interpretability*（Bryan Lim 等，钓鱼检测，与 GRPO 无关）。正确编号为 **2503.20783**：Understanding R1-Zero-Like Training: A Critical Perspective，Zichen Liu 等 8 人（Sea AI Lab／NUS／SMU），2025-03-26 / updated 2025-10-06（v2，COLM 2025） | 采用 2503.20783，并在本文件登记 |
| GSPO | 2507.18071 | **相符**：Group Sequence Policy Optimization，Chujie Zheng 等 12 人（Qwen Team, Alibaba Inc.），2025-07-24 / updated 2025-07-28（v2） | 采用 |
| TENT | 2006.10726 | **相符**：Tent: Fully Test-time Adaptation by Entropy Minimization，Dequan Wang 等 5 人（UC Berkeley／Adobe Research），2020-06-18 / updated 2021-03-18（v3） | 采用 |
| CoTTA | 2203.13591 | **相符**：Continual Test-Time Domain Adaptation，Qin Wang, Olga Fink, Luc Van Gool, Dengxin Dai（ETH Zurich／MPI-INF／EPFL／KU Leuven），2022-03-25 | 采用 |
| SAR | 2302.12400 | **相符**：Towards Stable Test-Time Adaptation in Dynamic Wild World，Shuaicheng Niu 等 7 人，2023-02-24（ICLR 2023） | 采用 |
| EATA | 2205.10296 | **不符**：2205.10296 实为 *Fermion dynamics in presence of non abelian monopoles*（Alejandro Morano, Osvaldo Santillán，高能物理，与 TTA 无关）。经题名检索得正确编号 **2204.02610**：Efficient Test-Time Model Adaptation without Forgetting，Shuaicheng Niu 等 6 人（ICML 2022），2022-04-06 | 采用 2204.02610，并在本文件登记 |

## 二、原件现状（去重结果，遵守 raw/AGENTS.md「已有原件只读、不改名」）

| 论文 | raw 路径 | 来源 |
|---|---|---|
| DeepSeekMath | `raw/papers/grpo/2402.03300.pdf`（30 页，已存在且题名核验相符） | 复用既有原件，不重复下载 |
| Dr. GRPO | `raw/papers/grpo/2503.20783.pdf`（20 页，已存在且题名核验相符，COLM 2025 版） | 复用既有原件 |
| DAPO | `raw/papers/grpo/2025-Yu-DAPO.pdf`（16 页，826,801 B，2026-09-10 15:07 下载） | 本次新增 |
| GSPO | `raw/papers/grpo/2025-Zheng-GSPO-Group-Sequence-Policy-Optimization.pdf`（7 页，458,773 B） | 本次新增 |
| TENT | `raw/papers/attack-detection/tent-iclr2021-wang.pdf`（15 页，主代理已下载） | 复用，本次核验题名相符 |
| CoTTA | `raw/papers/attack-detection/2022-Wang-CoTTA-Continual-Test-Time-Domain-Adaptation.pdf`（11 页，730,640 B） | 本次新增 |
| SAR | `raw/papers/attack-detection/2023-Niu-SAR-Stable-TTA-Dynamic-Wild-World.pdf`（27 页，1,713,390 B） | 本次新增 |
| EATA | `raw/papers/attack-detection/2022-Niu-EATA-Efficient-Test-Time-Model-Adaptation-Without-Forgetting.pdf`（17 页，961,492 B） | 本次新增 |

全部 8 份原件已用 `pypdf` 抽出首页题名并核对，与题录一致。

## 三、Zotero 现状（检索时间 15:09）

- 已存在：DeepSeekMath（item key `9WUKHNGP`，**作者字段为空、无年份**，疑似早期自动入库的残缺条目）；Dr. GRPO / Understanding R1-Zero-Like Training（item key `RQIJMDEG`，作者齐全但 `year` 字段为 `1784097959.0288706` 的异常值）
- 未收录：TENT、DAPO、GSPO、CoTTA、SAR、EATA

## 四、全文抽取

- `pypdf` 逐页抽取（带 `=== [PDF page N] ===` 页码锚点）全部 8 篇 → `/tmp/ch3lit/pages/<slug>.md`，用于**页码定位**
- `mineru-open-api flash-extract`（MinerU 开放 API，pdf-converter 技能指定入口）用于**公式保真**：本机无本地 MinerU，`mineru-open-api@0.5.9` 在 `~/.local/bin/`。限制 10 MB／20 页，SAR（27 页）与 DeepSeekMath（30 页）需按页段二次调用
- 抽取产物只作辅助；笔记中的公式、数字、页码一律回原文复核（wiki/AGENTS.md）

## 四之二、抽取模式裁决与重转登记（2026-09-10 15:12 收到主代理转达的用户裁决）

**裁决内容**：不得使用 `flash-extract`（免认证快速通道），一律使用正式 `extract`（全保真：图片、表格、LaTeX 公式）。

**执行与实测**：

- `mineru-open-api auth --verify` 返回 `Token format is valid / Source: env`，认证已由用户配置生效（未打印 token 本体）
- 先以 GSPO 单文件验证：`mineru-open-api extract raw/papers/grpo/2025-Zheng-GSPO-Group-Sequence-Policy-Optimization.pdf -o /tmp/ch3lit/extract/gspo --language en`，实测 **7.7 秒完成**，产出 `2025-Zheng-GSPO-Group-Sequence-Policy-Optimization.md`（29,253 B）＋ `images/`（23 项）。公式为真 LaTeX（例：`$\mathcal{J}_{\mathrm{PPO}}(\theta)=\mathbb{E}_{x\sim\mathcal{D},y\sim\pi_{\theta_{\mathrm{old}}}(\cdot|x)}[\frac{1}{|y|}\sum_{t=1}^{|y|}\min(w_t(\theta)\widehat{A}_t,\operatorname{clip}(w_t(\theta),1-\varepsilon,1+\varepsilon)\widehat{A}_t)]\tag{1}$`），可直接核对公式号
- **flash-extract 被中止**：此前以后台批量方式提交过 flash-extract，其中 **tent** 已完成（`/tmp/ch3lit/md/tent.md`，50.9 KB），其余（CoTTA/EATA/Dr.GRPO/DAPO/GSPO）在收到裁决时被 `TaskStop` 中止，未产出有效文件
- **重转登记**：以下文件一律改用 `extract` 重转（含已用 flash-extract 转出的 TENT）：
  TENT（重转）、CoTTA、EATA、SAR、DeepSeekMath、Dr. GRPO、DAPO、GSPO（GSPO 的 flash 版未产出，直接以 extract 首次转出）
- flash-extract 产物全部弃用，不进入笔记证据链
- 逐页 `pypdf` 文本（`/tmp/ch3lit/pages/*.md`，带 `=== [PDF page N] ===` 锚点）继续保留，**唯一作用是给出页码定位**；公式与数字的最终依据是 extract 产出的 LaTeX 与原始 PDF

## 五、进度日志

- 15:05 侦察目录与既有笔记格式（`wiki/papers/attack-detection/`、`wiki/papers/grpo/`）
- 15:06–15:08 arXiv API 核验 8 个编号，发现 2 处错误（Dr. GRPO、EATA）
- 15:07 下载 5 个新 PDF（DAPO/GSPO/CoTTA/SAR/EATA），全部核验题名与页数
- 15:09 Zotero 查重，pypdf 逐页抽取 8 篇完成
- 15:10 启动 MinerU flash-extract（6 篇，后台）
- 15:12 收到用户裁决（改用 extract 模式），中止 flash-extract，登记重转清单（见 §四之二）
- 15:12 GSPO 单文件验证 extract 模式（7.7 s，真 LaTeX）；15:12–15:30 批量 extract 全部 8 篇，全部 `Done`
- 15:35–16:40 写 8 篇 wiki 结构化笔记（GRPO 4 篇 → `wiki/papers/grpo/`；TTA 4 篇 → `wiki/papers/attack-detection/`）
- 16:45 Zotero 入库：6 篇新增（见下表），2 篇复用既有条目
- 16:50 更新索引：`wiki/papers/attack-detection/INDEX.md`（新增「TTA 家族机制来源」节）、新建 `wiki/papers/grpo/INDEX.md`、`wiki/INDEX.md` 增一行指向 GRPO 家族原文索引
- 16:55 交付核验：8 篇笔记 frontmatter 八字段齐全、`source_pdf` 全部指向存在的原件、均含「可迁移机制」与「不能直接声称内容」小节、两份 INDEX 的 wikilink 全部可解析

## 六、最终交付清单

### 原件（raw/）

| 论文 | 路径 | 来源 |
|---|---|---|
| DeepSeekMath | `raw/papers/grpo/2402.03300.pdf` | 复用既有 |
| DAPO | `raw/papers/grpo/2025-Yu-DAPO.pdf` | 本次下载 |
| Dr. GRPO | `raw/papers/grpo/2503.20783.pdf` | 复用既有 |
| GSPO | `raw/papers/grpo/2025-Zheng-GSPO-Group-Sequence-Policy-Optimization.pdf` | 本次下载 |
| TENT | `raw/papers/attack-detection/tent-iclr2021-wang.pdf` | 复用既有（主代理下载） |
| CoTTA | `raw/papers/attack-detection/2022-Wang-CoTTA-Continual-Test-Time-Domain-Adaptation.pdf` | 本次下载 |
| SAR | `raw/papers/attack-detection/2023-Niu-SAR-Stable-TTA-Dynamic-Wild-World.pdf` | 本次下载 |
| EATA | `raw/papers/attack-detection/2022-Niu-EATA-Efficient-Test-Time-Model-Adaptation-Without-Forgetting.pdf` | 本次下载 |

### 笔记（wiki/）与 Zotero

| 论文 | wiki 笔记 | Zotero item key |
|---|---|---|
| DeepSeekMath | `wiki/papers/grpo/2024-Shao-DeepSeekMath与GRPO开山.md` | `9WUKHNGP`（既有，元数据残缺：无作者/年份） |
| DAPO | `wiki/papers/grpo/2025-Yu-DAPO解耦裁剪与动态采样.md` | `ASPTA492`（新增） |
| Dr. GRPO | `wiki/papers/grpo/2025-Liu-DrGRPO无偏优化与R1-Zero再审视.md` | `RQIJMDEG`（既有，`date` 字段为异常值 `1784097959.0288706`） |
| GSPO | `wiki/papers/grpo/2025-Zheng-GSPO序列级重要性比率.md` | `LB624AXR`（新增） |
| TENT | `wiki/papers/attack-detection/2021-Wang-TENT熵最小化全测试时适应.md` | `XXSBBP6L`（新增） |
| CoTTA | `wiki/papers/attack-detection/2022-Wang-CoTTA持续测试时域适应.md` | `NHMIYSLX`（新增） |
| SAR | `wiki/papers/attack-detection/2023-Niu-SAR动态环境稳定测试时适应.md` | `EKK3NJLF`（新增） |
| EATA | `wiki/papers/attack-detection/2022-Niu-EATA无遗忘高效测试时适应.md` | `SRQX4FQM`（新增） |

### 待用户处置的两条 Zotero 元数据缺陷（本次未擅自改写既有条目）

1. `9WUKHNGP`（DeepSeekMath）：无作者、无日期、无期刊/会议字段，仅题名与标签（标签来自另一课题）。
2. `RQIJMDEG`（Dr. GRPO）：`date` 字段被写成 `1784097959.0288706`（纪元秒被塞进日期字段）；`journal` 记为 Findings of EMNLP 2025 且附 DOI `10.18653/v1/2025.findings-emnlp.1015`，而原件 PDF 页眉写的是 **COLM 2025**——两者不符，未核实哪个为准，登记待核。
