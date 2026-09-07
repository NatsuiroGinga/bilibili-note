# DRIFT-DGA 引用与方法前沿调研笔记

## 检索日志

### 2026-09-07：规则与技能检查

- 已读取：根、`raw/`、`wiki/`、`.Codex/docs/`、RWKV 路线规则与第三章恢复卡。
- 已读取技能：`planning-with-files`、`citation-verification`、`google-scholar`、`pdf-converter`、`huggingface-papers`、`hf-cli`。
- PDF 合同：性能数字、表格、公式与引用措辞必须用 MinerU `extract` 的全文结果辅助定位，并回到 PDF 页码复核；不得输出认证令牌。
- 题录合同：题名、作者、年份、标识符至少由两个独立元数据源交叉核验；方法与效果必须由全文核验。

### 2026-09-07：本地混合索引

- 状态命令：`status --json`；第一次状态为陈旧，原因是并行任务新增/修改过程文档，随后由混合查询触发增量重建。
- 可用收据：`built_at=2026-09-07T05:29:17.390008+00:00`，`source_manifest_hash=be68f60c6d85ef485416ad80b880312cf11cfce22318bba763a6b6bcd181bde2`，`index_sha256=be6187266bd063df2c9b537ad88d250d1aa8fdbee346fc61184dfeb7a50af97e`，当时复查 `stale=false`。
- 查询一：`DRIFT-DGA 2605.10436 drift26dsn`，作用域 `paper`，模式 `hybrid`。没有命中 DRIFT 原论文，首批结果均为通用漂移或无关论文。
- 查询二：`domain generation algorithm temporal drift unseen families future year`，作用域 `paper`，模式 `hybrid`。命中非平稳域泛化、恶意软件漂移、测试时适配等 C 类近邻。
- 查询三：`DGA concept drift dataset yearly false positive false negative`，作用域 `paper`，模式 `hybrid`。命中 OWAD、MADCAT 等 C 类近邻，但没有 A/B。
- 解释：本地全文库在查询时未收录 DRIFT，不能据此单独断言零引用；该结果只证明后续必须查 Zotero 和在线引用网络。

### 2026-09-07：Zotero 去重与全文状态

- 语义查询：`DRIFT-DGA 2026 domain generation algorithm temporal drift dataset unseen family`，前十项仅包含通用域适配、非平稳域泛化、网络入侵漂移等近邻。
- 精确题录查询：`DRIFT-DGA`、`2605.10436`、`drift26dsn` 均返回零项；因此 DRIFT 原论文在本轮开始时未入库。
- 已知现有全文条目由主代理实时核验：Engram `6QVYYE8Z`（PDF `YI925ABB`，95,901 字符）、mHC `289Y9PZM`（PDF `5VBB6LAV`，74,987 字符）、MalMoE `PUN5HXMA`（57,191 字符）、MADCAT `59GWHNT2`（29,239 字符）、Wasswa `CHMNFSNP`（33,717 字符）、Berruz `VQKRUFJV`（89,769 字符）。这些条目禁止重复导入。
- LSPR 三年序列条目 `U4ZMBMEK` 只有 474 字符笔记且无 PDF，不能作为全文证据。

### 2026-09-07：A/B 引用与使用网络阶段性结论

检索时点均为 2026-09-07。A/B 只统计独立后续论文或制品；作者自己的论文、数据、模型、代码和官方演示不计入 A/B。

| 来源 | 查询对象 | 结果 | 对 A/B 的含义 |
|---|---|---|---|
| Semantic Scholar Graph API | `ARXIV:2605.10436/citations` | `data=[]` | A=0 |
| OpenAlex API | DOI `10.1109/DSN69566.2026.00077`，工作 `W7167736745` | `cited_by_count=0` | A=0 |
| Crossref API | 同 DOI | `is-referenced-by-count=0` | A=0 |
| Scite | 同 DOI | 只返回原论文题录，未返回引用语句或引用统计 | 未发现 A |
| Google Scholar 可用 MCP 实现 | 精确题名、`2605.10436`、`dga-detection-drift26dsn`，各取 20 | 三组均零结果 | 未发现 A/B；本机 CLI 因无认证 Cookie 未采用 |
| GitHub 代码搜索 | 精确数据集标识、arXiv 号 | 两组均零结果 | 未发现第三方 B |
| GitHub 仓库搜索 | `DRIFT DGA detection` | 零结果；官方仓库另由稳定 URL 与 `git ls-remote` 核验 | 未发现第三方复现 |
| Web 精确检索 | 题名、arXiv 号、数据集标识、数据 DOI、论文 DOI | 只见 arXiv、IEEE/会议索引、作者/实验室页、官方 Hugging Face、CatalyzeX 等聚合页和一个数据集目录镜像 | 聚合/镜像不构成 A/B |
| Hugging Face 论文关联 | 论文页 `2605.10436` | 关联 1 个作者官方模型、1 个作者官方数据集、1 个演示空间 | 均是原工作发布链，不是后续 A/B |

**阶段性数量：截至 2026-09-07，已核来源中 A=0，B=0。** 因而不存在需要取得全文的 A/B 后续论文。后续若发现新候选，必须先取得全文并按必填字段复核，不能用 C 类论文替代。

### 2026-09-07：原论文与官方发布链

- 题名：*DRIFT: Drift-Resilient Invariant-Feature Transformer for DGA Detection*。
- 作者：Chaeyoung Lee、Chaeri Jung、Seonghoon Jeong。
- arXiv：`2605.10436v2`；DSN 2026 正式 DOI：`10.1109/DSN69566.2026.00077`；正式页码 786–799。
- arXiv v2 PDF 已下载到临时目录并用认证态 MinerU `extract` 成功解析；全文 14 页、8 表、7 图。
- 官方代码仓库：`https://github.com/snsec-net/2026-DSN-DRIFT`，本轮核验提交 `e20d1fdf56c623993966c6786f61c01f91dec6d2`，提交时间 2026-07-20。
- 官方 Hugging Face 数据集：`snsec-net/dga-detection-drift26dsn`，本轮核验提交 `3b31077020cd1c013d0a75cad51042a2327c4521`，最后修改 2026-07-20；官方模型：`snsec-net/dga-detector-drift26dsn`。

### 2026-09-07：原论文入库与 Zotero 验证

- 新增原件：`raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf`，SHA-256 `c955651911fc11daf09efff754eac1f6b925450c25b4ff68e9374a5445756d5c`。
- 新增严格全文笔记：`wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md`；`paper-note-search/v1` 严格检查为 0 错误、0 警告。
- 数据集索引已加入 DRIFT 条目。
- Zotero 导入主条目 `JJ5J9YR3`、PDF `WEHMI4PA`，附件全文 81,314 字符；导入后另出现无附件同题父项 `HMF49WET`，未在无授权下删除。
- Engram `6QVYYE8Z` 原先错误绑定无关放射肿瘤学 DOI/期刊，本轮保留 PDF `YI925ABB` 和父键，修正作者、日期、arXiv URL、错误 DOI/期刊与标签。
- mHC `289Y9PZM` 保留 PDF `5VBB6LAV`，补齐作者、日期、arXiv URL 与标签。
- LSPR Dijk 2025、Leoste 2025、Dijk 2026 的 Zotero 附件修复均因本地条目键在 Web API 用户库中不存在而返回 404；未通过重复导入父项规避。Dijk 2024 有附件但无正文索引。

### 2026-09-07：已有 DRIFT pilot 对机制优先级的影响

- 制品：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-t17-t25-rosa-deepembed-coverage-probe-v1/pilot-10000-rwkv-env.json`。
- 固定数据 revision：`3b31077020cd1c013d0a75cad51042a2327c4521`；模式 `pilot`，`T17/T25 × benign/DGA` 各 10,000 域名，共 40,000。
- ROSA/固定 N-gram 统计：1/2/3/4 元组重复覆盖分别为 `0.248060/0.017849/0.001923/0.000565`。长于极短局部模式的覆盖迅速衰减，支持把 ROSA 降为低优先条件候选。
- 该制品明确 `mechanism_adjudication=false`，不能据此正式淘汰 ROSA；DeepEmbed 标为未运行，raw 家族审计因 SQLite 路径未验收而禁用。
- 下一快速动作：同四分面运行 DeepEmbed 字符/2–3 元组 OOV、T17 频数长尾、T25 新生/消失键、哈希碰撞，并做 raw 家族支持计数；不先训练 ROSA 或 mHC。

## 候选分类表

| 候选 | 分类 | 发现来源 | 全文状态 | 纳入/排除理由 | 下一步 |
|---|---|---|---|---|---|
| DRIFT-DGA 2026 | 原论文 | arXiv、Crossref、OpenAlex、HF、官方代码 | 已取得并由 MinerU 解析 | 核心事实源；待入 raw/wiki/Zotero | 页码复核、三层入库 |
| 独立引用论文 | A | 多源引用网络 | 未发现 | 截至检索日为零 | 保留零结果与查询收据 |
| 第三方数据实际使用 | B | GitHub/HF/Web 精确标识检索 | 未发现 | 截至检索日为零 | 保留零结果与查询收据 |

## 原论文证据矩阵

| 证据项 | 结论 | PDF 页码/表/图 | 核验状态 |
|---|---|---|---|
| 训练/验证/测试年份 | 2017–2019 全量减每年验证留出用于预训练与微调；每年留出 15 万良性+15 万 DGA 验证；冻结后逐年测 2020–2025 | PDF pp. 794–795，§IV.1 与表 II 前 | 已核全文 |
| 数据预处理与版本 | Alexa/Tranco 良性、DGArchive DGA；小写、有效二级域提取、RFC 1035 字符过滤、有效二级域去重 | PDF pp. 788–793，§II.1、§III.1 | 已核全文；仓库数据提交另记 |
| 重复与家族隔离 | 全局是否跨年去重未明确报告；良恶交叉污染会从良性侧删除；训练 65 家族、测试独有 83 家族 | PDF pp. 788–789、794，§II.1、§IV.1 | 部分已核；跨年重复隔离缺失 |
| 目标标签权限 | 监督微调使用 2017–2019 标签；冻结未来年测试不参与模型训练；持续学习实验每年使用新标签 | PDF pp. 792–797，§III.3、§IV.1、§IV.4 | 已核全文 |
| 强基线 | Endgame、MIT、NYU、B-ResNet、M-ResNet+B-cos、Dom2Vec、HMT、Llama3-8B、HDDN、BERT，另含纯监督 DRIFT | PDF pp. 795–797，表 VI–VII | 已核全文；公平性仍有复现缺口 |
| 提出机制与任务化差量 | 字符/子词双分支 Transformer；MTP、TPP、TOV 三项自监督预训练；池化融合；两阶段微调 | PDF pp. 791–794，§III | 已核全文 |
| 按年 FPR/FNR/F1 | 表 VII 报逐年 FPR/FNR；F1 只报 2020–2025 微平均/图形趋势，未给逐年精确表 | PDF pp. 796–797，表 VI–VII、图 6 | 已核全文 |
| 未见家族结果 | 83 个测试独有家族上 DRIFT FNR=0.143913；MIT/NYU/HMT 为 0.279048/0.255106/0.259630 | PDF p. 797，表 VIII | 已核全文 |
| 消融与资源 | 表 II–V；RTX 5090，双骨干各 250 万预训练步，24/29 小时；140 万微调步约 22 小时；批量 128；推理 27,545.6 域/秒 | PDF pp. 794–796，§IV.1、表 II–V | 已核全文 |
| 单/多种子 | 正文与公开代码均未报告随机种子、重复次数、方差或置信区间 | 全文检索；官方仓库提交 `e20d1fdf…` | 已核：缺失 |

## 收尾状态

- 截至 2026-09-07 的多源引用与使用网络结论为 `A=0/B=0`；没有 A/B 全文条目，不能用 C 类替代。
- 官方年份角色已核；跨年同 eSLD、生成器等价和完整许可/字段一致性仍是实验合同阻断，不影响引用网络零结果。
- 总体 F1 不是唯一余量：原文未见家族 FNR `0.143913`；本课题 T17–T19 源期结果又发现最短形态组双侧恶化和分支异质性。
- ROSA 与源冻结后缀修补已由合法源期实验否决；条件记忆降为候补；方案 A `N10+N11` 与方案 B `N02+N09` 均只获病灶资格，训练机制仍待证。

### 2026-09-07：源期结果与综述收尾

- B-ResNet 总体/形态制品：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-bresnet-t17-t18-t19-source-tail-diagnostic-v1/formal-v1/result.json` 与 `morphology.json`；配置、8 输入、检查点和相互引用哈希均复算一致。
- 官方三支路结果：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-official-branch-conflict-t17-t18-t19-v1/result.json`，SHA-256 `91c72ca65914c3fca73da52aee45922406d023620082afc83ca420c2b0f8b3a8`；日志 SHA-256 `07f8e0a12d50c7ec1318830c797255fcbb54863bdf43aaa13b8021d83e937743`。
- 三支路只支持分支异质性/纠错空间和 N10 病灶资格；均值中和不是独立训练单支，启发式置信选择器在 AUROC/AP 与 FPR/FNR 交换上不利，不支持 N10 机制有效。
- 入库清单所列 11 份原件已重新计算 SHA-256，全部与登记一致。
