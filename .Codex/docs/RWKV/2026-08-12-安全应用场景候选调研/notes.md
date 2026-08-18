# 安全领域任务类型调研证据台账

- **日期**：2026-08-12
- **证据标记**：`[全文事实]`、`[正式题录事实]`、`[项目制品事实]`、`[本课题推论]`、`[待核验]`

## 查询与处理日志

### 2026-08-12：范围定义与路线恢复

- 已读取根规则、`.Codex/docs/AGENTS.md`、RWKV 局部规则、路线总控、当前恢复卡、候选登记册。
- 已读取 `planning-with-files`、`research-ideation`、`citation-verification` 及文献综述委派协议。
- 初始范围是机器遗忘邻近的十二类非静态流量任务；用户随后扩大为安全领域已被论文研究的完整任务盘点，不要求同一数据集。本文件保留此前已确认的 LSPR 项目事实，并在更大范围内继续检索。
- LSPR 数据族另设专项矩阵：同年二/多分类、跨年度泛化、跨场景或攻击留一、开放集未知攻击、持续学习与概念漂移、选择性预测、校准与固定告警预算、事件级检测与早期预警、攻击阶段与叙事溯源、机器遗忘、投毒或后门恢复、解释与主动学习。每项都需核验字段/标签支撑、论文/基线、饱和程度、协议缺陷和最小可证伪实验。
- 最终文档必须把文献事实、项目事实与本课题推论分列，不能用概念合理性替代全文或绑定数据实验。

## 已确认的当前项目事实

- `[项目制品事实]` LSPR24 同年、当前窗 XGBoost 验证 AP 为 `0.9690348794483452`，说明普通同年静态检测很强，但不能推出早期预警、拒识、校准、更新恢复等任务饱和。
- `[项目制品事实]` LSPR24 训练区与验证区正类率相差约 `2.15` 倍，存在时间先验变化；这为时间前向校准或预算告警研究提供现象依据，不证明任何方法有效。
- `[项目制品事实]` 修正活动键边界后，LSPR24 早期预警 B 任务三段正锚点为 `2883/1968/356`、独立前体簇为 `1025/753/158`，数据门禁通过；共享筛选视图切分口径仍需复核。
- `[项目制品事实]` LSPR23→LSPR24 跨年度强基线 AP 约 `0.0369–0.0389`，显著低于 LSPR24 同年 AP；跨域或漂移问题未饱和。
- `[项目制品事实]` LSPR24 筛选视图有 `label=-1`，占 `60.4075%`；所有监督评价只能在 `0/1` 标签上进行，未知标签不能直接当成新攻击类。

## 检索式日志

### 本地文件与知识库

- 待执行并逐条登记。

### Zotero

- 待执行并逐条登记。

### 联网正式来源

- 待执行并逐条登记。

## 文献证据记录字段

每条文献记录补齐：题名、作者、年份、发表源、DOI/arXiv、来源网址、本地原件路径、证据等级、全文位置、关键论断、纳入/排除理由、与任务候选关系、官方源码、Zotero 状态。

## 任务卡字段

每类任务补齐：任务定义；输入与输出；所需标签与数据；1—3 篇代表论文；常用数据集；正式强基线；主要指标；现有结果是否饱和；主要缺陷；理论与创新空间；数据与工程代价；当前本地数据是否可合法构造；毕业论文适配度；最小可证伪实验。

## 待办

- 盘点 GeNIS2025、TQH-C2、LSPR23/24 的本地数据说明、全文和既有综述。
- 盘点 `raw/`、`wiki/` 与 Zotero 中各任务的代表论文并去重。
- 完成正式网络题录、近期同构工作和官方源码核验。
- 逐类填充任务矩阵并完成前五排序。

## 2026-08-12 中断检查点

### 数量与完成度

- 六阶段：范围定义 `100%`；检索收集 `30%`；筛选分类 `18%`；全文分析 `15%`；综合空白 `5%`；制品生成 `8%`；总完成度约 `20%`。
- 已冻结 `20` 类任务：
  1. 开放集与未知攻击；
  2. 跨域与跨时间泛化；
  3. 持续学习与概念漂移；
  4. 机器遗忘；
  5. 数据投毒、后门检测与恢复；
  6. 对抗鲁棒；
  7. 选择性预测、拒识与风险覆盖；
  8. 概率校准与告警预算；
  9. 早期预警与最优停止；
  10. 攻击链阶段识别与溯源；
  11. 告警聚合与调查排序；
  12. 异常解释与根因定位；
  13. 主动学习、弱监督与少样本；
  14. 联邦与隐私保护检测；
  15. 威胁情报抽取与关联；
  16. 恶意软件行为分析；
  17. 日志异常；
  18. 漏洞发现与修复优先级；
  19. 欺诈、钓鱼与域名滥用；
  20. 模型水印、成员推断与数据审计。
- 最终任务卡完成 `0/20`；约 `7/20` 已定位本地候选来源，均仍需本轮题录、全文位置、任务协议和代表性复核。
- LSPR 直接使用研究已复用既有审计核验 `4` 项：Dijk 2024、Dijk 2025、Leoste 2025、Dijk 2026。
- LSPR 专项 `12` 个子任务完成约 `15%`；矩阵文件尚未创建。

### 已完成查询式与来源

#### 本地文件与知识库

- 文件名查询：`fd -t f . .Codex/docs/RWKV raw wiki | rg -i 'LSPR|Leoste|Dijk|GeNIS|TQH'`。
- 主题文件查询：`fd -t f . raw wiki .Codex/docs | rg -i 'unlearn|遗忘|open.?set|开放集|unknown.attack|未知攻击|concept.?drift|概念漂移|continual|持续学习|selective|拒识|calibrat|校准|poison|投毒|backdoor|后门|adversarial|对抗|federat|联邦|member.*infer|成员推断|early.?warn|早期预警|root.?cause|根因|active.?learn|主动学习|threat.intel|威胁情报|malware|恶意软件|log.anomal|日志异常|vulnerab|漏洞|phish|钓鱼|watermark|水印'`。
- 正文查询：`rg -i -l 'open set|unknown attack|concept drift|continual learning|machine unlearning|selective prediction|risk.coverage|early warning|attack chain|alert priorit|root cause|active learning|weak supervision|few.shot|federated|threat intelligence|malware behavior|log anomaly|vulnerability priorit|phishing|domain abuse|membership inference|watermark' wiki .Codex/docs`。
- 已回读的 LSPR 核心材料：
  - `.Codex/docs/RWKV/2026-08-11-LSPR直接使用论文查全审计.md`
  - `.Codex/docs/RWKV/2026-08-11-LSPR直接使用论文查全审计-notes.md`
  - `.Codex/docs/RWKV/2026-08-08-LSPR24使用论文任务与指标综述.md`
  - `.Codex/docs/RWKV/2026-08-08-LSPR24使用论文调研-notes.md`
  - `.Codex/docs/RWKV/2026-08-12-LSPR完整基线登记册.md`
- 已回读的非 LSPR 代表材料：开放集入侵识别笔记、RTTDP 现实测试时投毒笔记、Guo 置信度校准笔记、Minerva 威胁情报笔记，以及既有数据协议检索日志和证据表。

#### Zotero

- 状态查询：本地接口、连接器均为可用状态，只读使用。
- 已执行主题查询共 `20` 条：`LSPR23`、`open set intrusion`、`concept drift intrusion detection`、`machine unlearning intrusion`、`backdoor intrusion detection`、`selective prediction cybersecurity`、`calibration intrusion detection`、`early warning cyber attack`、`attack chain detection`、`alert prioritization cybersecurity`、`root cause log anomaly`、`active learning intrusion detection`、`federated intrusion detection`、`cyber threat intelligence extraction`、`malware behavior analysis`、`log anomaly detection`、`vulnerability prioritization`、`phishing detection`、`membership inference security`、`model watermarking`。
- 结果：`LSPR23` 命中同一 Dijk 2024 记录的三个重复条目；`open set intrusion` 命中 Cruz 2017；`log anomaly detection` 命中一条年份元数据异常记录，未纳入；其余查询为空。未执行 Zotero 写入、导入或合并。

#### 联网正式来源

- 本轮新增联网批量检索尚未开始即收到中断要求。既有 LSPR 查全审计已覆盖 Zenodo/DataCite、Crossref、OpenAlex、出版社、SSRN、作者页与引用链；续接时应先复用其查询日志，不重复全量查全。

### 已确认且必须保留的证据边界

- `[项目制品事实]` LSPR24 同年当前窗 XGBoost 验证 AP=`0.9690348794483452`；这是同年开发协议结果。
- `[全文事实]` Dijk 2026 报告 LSPR23→LSPR24 的跨年 AP 明显下降；本项目共同合同 Q0 的跨年 AP 约 `0.0369–0.0389`。两者协议不同，均不得与同年 AP 混成同一“性能水平”。
- `[项目制品事实]` LSPR24 标签包含 `-1/0/1`，`-1` 不能直接当作未知攻击类。
- `[项目制品事实]` 修正活动键边界后，早期预警 B 任务事件数量门禁通过，但共享筛选视图切分口径尚待独立复核。
- `[全文事实]` Cruz 2017 支持开放集协议必须让测试未知攻击类型在训练中不可见；是否能在 LSPR 上合法构造仍是本课题推论，需先核验原生攻击子类标签。
- `[全文事实]` Guo 2017 的温度缩放依赖独立验证集且原实验假定同分布，不能直接作为漂移下校准充分方案。
- `[全文事实]` RTTDP 2025 说明低熵、连续突发的测试时投毒能绕过简单熵阈值；原实验为视觉分类，不能直接声称适用于 LSPR。

### 未关闭证据卡

- 通用任务 `20` 类均未完成最终证据卡；尤其持续学习、机器遗忘、选择性预测、告警运营、根因定位、联邦隐私、恶意软件、漏洞与钓鱼等仍缺本轮代表论文全文核验。
- 已定位但未纳入完成计数：Cruz 2017、Guo 2017、RTTDP 2025、Minerva 2026，以及本地跨数据集泛化论文；需补题录核验、全文锚点、数据集、强基线和指标。
- LSPR `12` 子任务逐项字段/标签合法性尚未写成矩阵；机器遗忘、投毒恢复、解释、主动学习等方向很可能需要人工构造协议，不能预先写成“数据原生支持”。
- GeNIS2025 和 TQH-C2 的逐版引用与数据事实由并行专项代理负责，本任务续接时只消费其最终核验结果，不重复专项查全。

### 阻塞、下一动作与交付状态

- **阻塞**：无资料访问硬阻塞；因会话中断暂停。Zotero 命中稀疏是覆盖限制，不是系统故障。
- **唯一下一动作**：先重读本计划与台账，然后基于既有 LSPR 查全审计、三篇模型实验全文笔记、LSPR24 发布论文、数据合同和完整基线登记册，生成 `.Codex/docs/RWKV/2026-08-12-LSPR安全任务机会矩阵.md` 的 `12` 行完整矩阵；不得先恢复宽泛联网检索。
- **通用总览预定路径**：`.Codex/docs/RWKV/2026-08-12-安全应用场景候选调研/安全领域任务类型系统调研.md`，当前不存在。
- **LSPR 专项预定路径**：`.Codex/docs/RWKV/2026-08-12-LSPR安全任务机会矩阵.md`，当前不存在。

## 2026-08-12 恢复后：LSPR 专项完成记录

- 已生成 `.Codex/docs/RWKV/2026-08-12-LSPR安全任务机会矩阵.md`，共 294 行、12/12 项任务卡。
- 每项包含输入/输出、字段与标签合法性、现有论文/强基线、指标、饱和判断、协议缺陷、最小可证伪实验和毕业论文适配判断。
- 已明确区分三类协议：Dijk 2026 的 LSPR24 同年 `AP=0.9923`；项目 408 字段筛选视图同年诊断 `AP=0.9690348794483452`；LSPR23→24 跨年度公开/项目结果。三者不作直接方法胜负混排。
- 审查修订后，跨年度方向不再写成无条件“强推荐”：研究问题和任务指标未饱和，但本项目共同输入上的多轮 Q0 为弱不利。
- 已纳入项目筛选证据：共享 XGBoost `AP=0.038902589823969644`；TL1 最佳 `AP=0.039087019199325335`，相对锚仅 `+0.000184429375355691`，恶意召回 `1/2020`；R1 最佳 `AP=0.012877901366876719`；C12-R 最高 `AP=0.009274477710716156` 且恶意 F1/召回为 0；候选 B `0.019205959409695748→0.010123021167351991`。这些均为 `formal_paper_evidence=false` 的单种子 Q0，不是正式证伪。
- 当前跨年模型实验门禁：先核验标签可识别性、77/155 维合法字段可识别性和误差集中靶子；没有明确靶子时暂停模型轮换。
- 最小验证：12 个 `### 5.x` 小节齐全；`git diff --check` 无诊断；本地核心链接已列出并由既有文件支撑。
- 下一动作转为跨数据集 20 类安全任务的正式文献证据卡与最终前五排序。

## 2026-08-12 实验前冻结检查点

- **状态**：`CHECKPOINT_FOR_EXPERIMENT`。
- **LSPR 专项交付**：`.Codex/docs/RWKV/2026-08-12-LSPR安全任务机会矩阵.md` 已定稿，含 `12/12` 项任务卡；这是数据与实验门禁矩阵，不是方法效果报告。
- **跨年度任务裁决**：
  - `[全文事实]` 公开研究证明 LSPR23→LSPR24 跨年性能显著退化，因此研究问题重要且任务指标未饱和。
  - `[项目制品事实]` 共享 XGBoost `AP=0.038902589823969644`；TL1 最佳 `AP=0.039087019199325335`、仅增 `0.000184429375355691`，恶意召回 `1/2020`；R1、C12/C12-R 和候选 B 也均未通过 Q0 晋级门。
  - `[本课题推论]` 上述弱不利证据不正式证伪跨年度任务，但足以暂停无靶子的模型轮换。下一实验应优先证伪标签是否可由合法输入识别、共同字段是否丢失关键语义、误差是否集中在可行动分面。
- **实验边界**：本任务不改实验代码、不启动实验；真实实验制品必须由主任务按现有路线合同执行。本调研等待其配置、日志、指标和制品路径后再更新证据等级。

### 暂停前最后一批网络查询

以下查询已执行，但因转入实验检查点而停止筛选。结果只作为续接线索，**未计入已核验全文或最终任务卡**：

| 查询式 | 正式/原始来源线索 | 当前状态 |
| --- | --- | --- |
| `site:arxiv.org "Open Set Intrusion Recognition"` | Cruz 等 2017，arXiv:1703.02244；本地已有全文与笔记 | 已有全文，但通用任务卡未完成 |
| `site:usenix.org TESSERACT eliminating experimental bias malware classification space time` | Pendlebury 等 2019，USENIX Security，官方论文页与 PDF | 官方全文线索，待逐页证据卡 |
| `continual learning concept drift intrusion detection official paper` | SSF，arXiv:2412.16264/IEEE；METANOIA，arXiv:2501.00438；RepShield，DOI `10.1016/j.comnet.2026.112308` | 仅题录/摘要线索，待全文核验与去重 |
| `selective classification abstention intrusion detection cybersecurity paper` | Pietraszek 2007，*Classification of intrusion detection alerts using abstaining classifiers* | 出版社题录线索，待全文与数据协议核验 |

- **唯一后续文献动作**：实验门禁结果返回后，先回读本 `task_plan.md`、`notes.md` 与 LSPR 矩阵，把真实结果写成新的项目证据记录；随后从上表的 TESSERACT/SSF/METANOIA/拒识分类线索开始“分布变化与可信决策”批次，逐篇回到官方全文，不再重新搜索 LSPR、GeNIS 或 TQH-C2。
