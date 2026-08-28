# TQH-C2 相似数据集与可迁移任务六阶段文献综述计划

- **代理名**：`/root/tqhc2_analog_datasets_literature_sol_max`
- **模型**：`gpt-5.6-sol`
- **推理强度**：`max`
- **路线**：`RESEARCH_ROUTE=RWKV`
- **创建日期**：2026-08-12

## 目标与预期决策

以已核验的 TQH-C2 v1.2.0 特征画像为锚点，独立检索并全文分析相似数据集及其使用论文，区分“数据相似”与“任务／方法相似”，最终形成可追溯的相似数据集矩阵，并筛出三个能在 TQH-C2 上用最小实验直接证伪的方案。

## 冻结研究问题

1. 哪些公开数据集在捕获组、协议、标签、时间／版本、原始包／流模态和字段上与 TQH-C2 真正可比？
2. 哪些论文提供了可迁移的跨捕获／跨网络／跨数据集泛化协议，而非随机逐流切分？
3. 哪些论文在跨域校准、固定告警预算或选择性拒识上给出可复现实验合同？
4. 哪些论文严格使用因果流前缀评价早识别，并同时报告时延／包预算和完整流上界？
5. 哪些论文把未知恶意流量定义为训练期未见家族、域或协议，并同时评价已知类效用与未知拒识？
6. 哪三个机制与 TQH-C2 的现有模态、分组键和标签最匹配，且不会把数据集缺失的真值伪造出来？

## TQH-C2 冻结画像

- A：Sliver、TLS-over-TCP；B：Merlin、HTTP/3-over-QUIC；C：Mythic Poseidon、HTTP 加密体；D：Merlin、HTTP/2-over-TLS；每个成员 12 个完整捕获，共 48 个 `capture_id`。
- 目标为 `malicious_c2` 对非 C2；没有原生未知攻击类，`unknown=0` 且历史含义是传输／基础设施噪声。
- 原件含 PCAP、逐流 JSONL／Zeek、27 列 Parquet、清单；D 标签包缺 Zeek 日志。
- 默认共同输入为 7 个大小／计数字段；`capture_id` 只用于安全分组，`ts` 只用于因果排序与告警时长口径。
- 已观测：域内 HGB／XGBoost 宏 F1=`0.999618`；A+B→C 与 A+B+D→C 宏 F1=`0.128186–0.146574`，恶意召回=`0–0.003272`。这些是单种子开发诊断，不是正式方法结论。

## 纳入、排除与证据标准

### 纳入

- 数据集／基准原论文或官方规范记录，且至少能核验六项相似维度中的两项。
- 五条检索轴上有明确数据、切分、特征、基线、指标和结果的原论文。
- 核心结论必须来自全文；题录、摘要或网页只可作为召回线索或访问阻塞记录。
- 时间不限；优先 2020–2026 年，并保留定义任务或评价协议所必需的早期基础工作。

### 排除

- 只在随机逐流切分上报告接近满分，且无法恢复捕获／家族／时间分组的论文，不作为泛化证据。
- 只按名称声称与 TQH-C2 相似、没有协议／标签／捕获／模态证据的数据集。
- 只做应用识别、明文入侵或载荷语义分析，且输入不能映射到 TQH-C2 合法可观测量的方法。
- 只有搜索摘要、二手综述或宣传页而无全文的候选，不进入最终机制排序。

### 六维数据相似度

每项 `0–2` 分，总分 `0–12`：捕获组结构、协议与加密层、标签语义、时间／版本结构、原始包与流模态、可比字段。`8–12` 为高数据相似，`5–7` 为中等，`0–4` 只可列作任务／方法相似。总分不替代逐项理由。

## 六阶段与检查点

- [x] **阶段 1：范围定义**——完整读取规则、RWKV 恢复链、相关技能和现有 TQH-C2 审计；冻结问题、画像、六维评分、纳排标准、输出和停止条件。
- [ ] **阶段 2：检索与收集**——先查本地 `raw/wiki/.Codex/docs` 与 Zotero 去重，再沿五轴联网检索原论文／官方数据记录；保存查询式、标识符和候选状态。
- [ ] **阶段 3：筛选与分类**——按数据相似、任务相似、方法相似、排除、待补全文分类；逐项填写六维相似度与纳入理由。
- [ ] **阶段 4：全文分析**——每篇提取数据、切分、特征、基线、指标、缺陷、可迁移机制和 TQH-C2 最小实验映射；记录页码／章节／表格位置。
- [ ] **阶段 5：综合与研究空白**——建立跨论文比较矩阵，识别一致证据、冲突、不可比项和真实空白；形成前三可证伪方案。
- [ ] **阶段 6：制品生成与验收**——新增全文写入 `raw/papers/`，结构化笔记写入 `wiki/papers/` 并更新索引；核验 Zotero；完成相似数据集矩阵、综述和缺失全文清单。

## 检索轴与初始关键词

1. **加密 C2／恶意 TLS 或 QUIC**：`encrypted command and control traffic dataset`、`malicious TLS dataset`、`malicious QUIC detection dataset`、`DoH DoQ C2 detection`。
2. **跨捕获／跨网络／跨数据集泛化**：`cross dataset encrypted traffic classification`、`cross network intrusion detection generalization`、`leave one capture out malware traffic`。
3. **跨域校准／告警预算／选择性拒识**：`network intrusion calibration domain shift`、`selective classification intrusion detection`、`risk coverage out of distribution network traffic`、`false alerts per hour`。
4. **流前缀早识别**：`early encrypted traffic classification first packets`、`traffic classification packet prefix`、`early malicious traffic detection latency`。
5. **开放集未知恶意流量**：`open set intrusion detection unseen attacks`、`open world encrypted traffic classification`、`unknown malware traffic rejection`。

## 目标规模与停止条件

- 目标纳入 `12–18` 个原始来源，其中数据集／基准来源至少 `5` 个，五条轴每条至少 `2` 个全文证据；同一论文可覆盖多轴。
- 每完成 `3–4` 篇全文，立即更新 `notes.md` 与本计划的数量和状态。
- 关键数据集候选均完成六维评分；每个最终方案至少由两篇互补原论文支持，并有明确的 TQH-C2 可观测量、基线、指标和失败门槛。
- 连续两轮扩展检索不再新增会改变前三方案或数据集排序的核心全文后停止。
- 所有最终提及论文都有 `raw/` 原件或精确访问阻塞；所有实际取得全文都有 `wiki/` 笔记与索引入口；Zotero 状态不虚报。

## 输出路径

- 过程笔记：本目录 `notes.md`
- 相似数据集矩阵：本目录 `TQH-C2相似数据集矩阵.md`
- 最终综述：本目录 `TQH-C2相似数据集与可迁移任务文献综述.md`
- 缺失全文清单：本目录 `缺失全文与人工下载清单.md`
- 原始全文：`raw/papers/datasets/`、`raw/papers/encrypted-traffic/` 或既有最匹配子目录
- 结构化笔记：`wiki/papers/datasets/`、`wiki/papers/encrypted-traffic/` 或既有最匹配子目录

## 禁止变更

- 不修改 `RWKV路线总控.md`、`RWKV当前恢复卡.md`、`2026-08-08-第三章候选方案登记册.md`。
- 不修改实验代码、配置或数据合同，不启动实验。
- 不把文献机制可迁移性写成 TQH-C2 上已有效。

## 决策记录

- 直接引用／使用 TQH-C2 的查全由相邻任务负责，本任务不重复检索；只复用其已核验画像和 `A/B=0` 的截止日结论。
- 候选数据集先按六维事实评分，再判断任务或方法迁移价值；热门度和名称不参与评分。
- 开放集与流前缀任务均是代理任务：前者只能留一框架／成员作未见域，后者只能继承完整流标签，禁止声称原生未知攻击或攻击开始时刻。

## 错误与阻塞

- 初次在受限沙箱内创建本任务目录返回 `Operation not permitted`；已通过指定路径授权创建，未触及其他目录。

## 当前状态

**因会话中断暂停于阶段 2**：阶段 1 已完成；本地／Zotero／联网候选发现各完成一轮，4 篇本地全文已核验但逐篇证据卡和六维评分尚未完成。未下载新原件，未写入 `wiki/`、索引或 Zotero，未启动实验。精确完成度、候选状态、数量、阻塞和恢复动作见 `notes.md` 的“检查点 1”。

**唯一恢复动作**：先为 CBSeq、Lichy、Cruz、H23Q 补齐逐篇证据卡与六维分数并保存首个 4 篇检查点；完成前不继续联网召回。
