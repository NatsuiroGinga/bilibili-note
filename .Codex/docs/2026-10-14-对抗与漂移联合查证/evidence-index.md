# 证据索引：对抗与漂移联合查证（2026-10-14）

> 每条给出：来源、URL/路径、证据等级、关键页码/锚点、支撑哪一问。

## 本地制品（ch3-drift-20260908 工作树，只读）

| # | 来源 | 路径 | 等级 | 关键锚点 | 支撑 |
| --- | --- | --- | --- | --- | --- |
| 1 | Cortellazzi et al., *Intriguing Properties of Adversarial ML Attacks in the Problem Space*（S&P 2020 扩展版，arXiv:1911.02142v3） | 原件 `raw/papers/attack-detection/2019-Cortellazzi-Problem-Space-Adversarial.pdf`；笔记 `wiki/papers/attack-detection/2019-Cortellazzi-问题空间对抗攻击与约束.md` | 本地结构化全文笔记 | 四约束定义 8–12 p.7–8；投影单调性 p.9；副效应特征 p.8–9；`check_feasibility` 权限规则 §3.6 p.15；对抗重训失效 p.21；问题空间样本硬化更优 p.21–22 | Q3 |
| 2 | El-Hajj & Zeineddine 2026（Front. Artif. Intell. 9:1811692） | `wiki/papers/attack-detection/2026-El-Hajj-Malware-MultiScale-LOEO-MLOps-全文.md` | 本地结构化全文笔记 | 行 150 表 1（Drift exploitation 维度）；行 156 漂移加速公式；行 180「Trigger false drift detection」；行 242 Sandor 转述；行 1573 Sandor 参考文献全条 | Q1、Q3（feasibility constraint 形式化旁证） |
| 3 | LAMDA 原论文证据记录（arXiv:2505.18551） | `wiki/papers/datasets/2026-Haque-LAMDA-Android恶意软件长期漂移基准.md` | 本地结构化全文笔记 | Evidence ID `LAMDA-E1`；`rg -i adversar` 零命中 | Q4 |
| 4 | LAMDA 相关工作综述（14 条引用核验） | `wiki/papers/malware/LAMDA-2026-原论文与时间漂移相关工作综述.md` | 本地结构化全文笔记 | 行 132–142 直接近邻表；`rg -i adversar` 零命中 | Q4 |
| 5 | 本地综述 PAD 声称 | `thesis/methods/第三章-LAMDA主任务与机制裁决.md` 行 48；`thesis/methods/第三章-LAMDA任务与方案筛选矩阵.md` 行 160 | 本地裁决文档（声称，未附原件） | 「PAD 2023（TDSC）已占恶意软件对抗训练的收敛保证」 | Q2（被核对象） |
| 6 | PAD OpenAlex 记录（本地制品） | `.Codex/docs/2026-10-14-理论算法家族综述/raw-queries/openalex/abs_PAD.json` | 本地在线题录制品 | 题名/年份/期刊/DOI/摘要全 | Q2 |

## 在线来源（当日核验）

| # | 来源 | URL | 等级 | 关键内容 | 支撑 |
| --- | --- | --- | --- | --- | --- |
| 7 | PAD arXiv 全文 HTML（v2） | `arxiv.org/html/2302.11328v2` | 在线全文已核 | §III-A 威胁模型（白盒规避、非功能性指令）；box 约束（非 norm 球）；Theorem 2 收敛率 O(1/√N)；Drebin+Malscan 数据集；rg 漂移词汇零命中 | Q2 |
| 8 | PAD OpenAlex DOI 直查 | `api.openalex.org/works/doi:10.1109/tdsc.2023.3265665` | 在线题录 | TDSC 2023，被引 40；OA=arXiv:2302.11328 | Q2 |
| 9 | Şandor et al. ICCP 2024 OpenAlex 直查 | `api.openalex.org/works/doi:10.1109/ICCP63557.2024.10793037` | 在线摘要（倒排重建） | 摘要全文：feature engineering + adversarial training + training data mutations；被引 1 | Q1 |
| 10 | TAH-GAN 预印本 Crossref 直查 | DOI `10.21203/rs.3.rs-10821022/v1` | 在线摘要 | time-aware GAN、drift-aware robustness assessment、KronoDroid+AndroMD | Q1 |
| 11 | LAMDA S2 引用面（14 条） | `api.semanticscholar.org/graph/v1/paper/arXiv:2505.18551?fields=...citations` | 在线题录+标题 | 14 条逐条判读；唯一对抗向=DeepTrust | Q4 |
| 12 | DeepTrust arXiv 全文 HTML | `arxiv.org/html/2510.12310`（ESWA 2026，DOI 10.1016/j.eswa.2026.132961） | 在线全文已核 | `rg LAMDA` 零命中；实验在 ELSA-RAMD（DREBIN 特征 d=1,461,078）；Track 1 特征空间攻击；参考文献 [10][11]=ELSA-RAMD 基准+SaTML'25 竞赛 | Q3、Q4 |
| 13 | Zainab et al. arXiv 全文 HTML | `arxiv.org/html/2609.34456v1` | 在线全文已核 | Windows PE；可执行性约束使 Gamma-section 攻击 ASR 大降（§讨论） | Q3 |
| 14 | Demetrio et al. arXiv 摘要 | `arxiv.org/abs/1901.03583` | 在线摘要 | Windows PE 特征归因+对抗二进制（SecML Malware 线） | Q3 |
| 15 | REPLICANT arXiv 摘要 | `arxiv.org/abs/2608.28499` | 在线摘要 | deep RL 真实规避策略；摘要无时间维 | Q1（排除项） |
| 16 | Google Scholar 检索页（多组） | `scholar.google.com/scholar?q=...` | 在线检索记录 | 三个精确短语零命中（PAD 错题录）；`"adversarial training" "concept drift" malware` 命中 TAH-GAN/REPLICANT/HYDRA | Q1、Q2 |
| 17 | Crossref DOI 核验（2 条） | `api.crossref.org/works/10.1109/TDSC.2023.3271837`、`.../10.1109/TDSC.2022.3175541` | 在线题录核验失败记录 | 均 404（错 DOI） | Q2（误判过程） |
| 18 | Zotero 语义检索 | MCP `zotero_semantic_search` | 本地库 | 漂移侧齐全、无联合工作、无 Sandor、无 PAD | Q1 |

## 检索式与零命中记录（Q4 负结果的一部分）

- 本地混合索引：`LAMDA dataset adversarial evaluation android malware benchmark`、`LAMDA malware dataset time decay adversarial` → 无对抗评价命中（索引 built 2026-10-14T03:16Z，stale=false，1934 notes）。
- Zotero：`adversarial robustness malware concept drift temporal evolution joint` → 无联合工作。
- S2 引用面 14 条标题全扫 → 无 LAMDA 对抗评价。
- 本地两份 LAMDA 笔记 `rg -i adversar` → 零命中。
