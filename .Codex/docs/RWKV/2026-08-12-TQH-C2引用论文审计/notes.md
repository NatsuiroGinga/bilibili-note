# TQH-C2 引用论文审计过程笔记

- **代理名**：`/root/tqhc2_citation_literature_sol_max`
- **模型**：`gpt-5.6-sol`
- **推理强度**：`max`
- **日期**：2026-08-12

## 检查点 0：任务合同

### 已知稳定标识符

| 对象 | 标识符 | 初始状态 |
| --- | --- | --- |
| TQH-C2 v1.2.0 | `10.5281/zenodo.21523144` | Zenodo 官方版本链已核验 |
| 概念记录 | `10.5281/zenodo.21330094` | 只作全版本聚合标识，不自动归入最新版 |
| v1.0.0 | `10.5281/zenodo.21330095` | Zenodo 官方版本链已核验 |
| v1.0.1 | `10.5281/zenodo.21435571` | Zenodo 官方版本链已核验 |
| v1.0.2 | `10.5281/zenodo.21436858` | Zenodo 官方版本链新增发现 |
| v1.1.0 | `10.5281/zenodo.21484904` | Zenodo 官方版本链新增发现 |

### 父任务提供的历史先验（仅作待复核线索）

- `.Codex/docs/2026-08-06-加密恶意流量检测论文实验论证综述.md` 第 149–153 行曾记录：DataCite `citationCount=0`、OpenAlex `W7169650382` 的 `cited_by_count=0`、Crossref 无精确命中、GitHub 未核验到外部复现。
- 当前任务必须重新核验，且分别检查 v1.2.0、概念记录和早期版本，防止版本引用聚合造成漏引。
- Web 通用精确查询当前先验仅返回 Zenodo 自身；尚不能据此得出“无人使用”。

### 证据等级

- `E3`：全文/补充材料/代码直接证据，可支持 A 类实验细节。
- `E2`：正式题录、引用关系元数据或出版社/作者页，可支持作品存在与引用关系，但不能独立支持实际使用。
- `E1`：摘要、搜索摘要、索引片段，只作召回与待核验线索。
- `E0`：推测或无法追溯结果，不进入结论。

## 查询批次日志

后续每批查询立即追加：时间、来源、查询式、结果数、去重后候选、证据等级、原件路径、纳入/排除理由、与本课题关系、待办和 Zotero 状态。

### 批次 1：本地仓库与 Zotero 去重（2026-08-12）

- **来源**：`raw/`、`wiki/`、`.Codex/docs/`、`thesis/`、Zotero Desktop 本地 API。
- **查询式**：`TQH-C2`、`TQHC2`、`TQH C2`、`10.5281/zenodo.21523144`、`10.5281/zenodo.21330094`、`10.5281/zenodo.21330095`、`10.5281/zenodo.21435571` 及对应记录号；文件检索使用 `fd`，正文检索使用 `rg`。
- **结果**：文本命中 288 个文件，主要是本课题的实验、设计与过程文档；`raw/papers/` 没有以 TQH-C2 或这些标识符命名的论文原件，`wiki/papers/` 没有对应全文论文笔记。官方数据制品已位于 `raw/datasets/TQH-C2-v1.2.0/`，至少含 README、校验和、A/B/C/D 特征、标签和 PCAP 压缩包。
- **既有综述**：`.Codex/docs/2026-08-06-加密恶意流量检测论文实验论证综述.md` 第 143–156 行记录 2026-08-06 的外部使用检索为 0；这是历史检查点，本轮重新核验。
- **Zotero**：本地 API 与 Connector 均可用。精确查询只有数据集条目 `AHY833JP`，题名为 `TQH-C2: An Encrypted Command-and-Control Traffic Dataset Across Protocols and Encryption Layers`，作者 Deokjo Jeon、DongGue Park，年份 2026。其 BibTeX 仍指向 `10.5281/zenodo.21330095`、版本 1.0.1，且无子项/PDF；未检得独立发布论文条目。
- **证据等级**：仓库与 Zotero 状态为 `E2`；不能据此断言不存在外部论文。
- **去重结论**：官方数据记录只算一个版本化作品；四个 DOI 必须按概念记录和版本关系聚合，不得当作四篇来源。
- **待办**：以官方 Zenodo/DataCite 元数据确定规范题名、版本、作者和关联关系；查询所有 DOI 的前向引用。

### 批次 2：父任务插件精确检索回传（2026-08-12）

- **Scite**：查询 DOI `10.5281/zenodo.21523144` 与 `10.5281/zenodo.21330095`；结果均为 0，且 DOI 未进入 Scite 索引。证据等级 `E1/E2`；只能说明该插件当前无可用引用记录。
- **Sider Scholar**：查询精确题名、`TQH-C2` 和题名变体；返回 `papers=[]`。证据等级 `E1`。
- **Consensus**：字面查询为 `"TQH-C2" encrypted command-and-control traffic dataset protocols encryption layers`；返回 `results=[]`。证据等级 `E1`。
- **SciSpace**：字面查询为 `Which scholarly papers cite, benchmark on, reproduce, or experimentally use the dataset titled "TQH-C2: An Encrypted Command-and-Control Traffic Dataset Across Protocols and Encryption Layers", including Zenodo DOIs 10.5281/zenodo.21523144 and 10.5281/zenodo.21330095?`；返回 10 篇语义邻近作品：
  1. `Botnet Detection Through Periodic Patterns in Command-and-Control Network Traffic`
  2. `Hierarchical Byte-Level Modeling via CNN and Mamba for Encrypted Traffic Classification`
  3. `Offloading Encrypted C2 Traffic Mitigation to SmartNICs`
  4. `Network-based anomaly detection in encrypted data streams: A cryptanalysis perspective`
  5. `SafeSurf Darknet 2025: A Novel Dataset for Darknet Traffic Detection and Analysis`
  6. `Design of Methods for Encrypted Traffic Visualization`
  7. `Interpretable Anomaly Detection in Encrypted Traffic Using SHAP with Machine Learning Models`
  8. `Deep learning for encrypted traffic classification in the face of data drift: An empirical study`
  9. `Detecting Stealthy Cobalt Strike C&C Activities via Multi-Flow based Machine Learning`
  10. `Machine Learning for Encrypted Malicious Traffic Detection: Approaches, Datasets and Comparative Study`
- **分类**：上述 10 篇均发表于 2022–2025 年，早于 TQH-C2 公开，因此不可能引用或使用该数据集，全部按本任务的引文/使用问题归为 `C 类：语义邻近误命中`。它们可进入邻近方法池，但不进入本次“使用数量”；本任务不在最终报告逐篇展开其方法，避免触发无关全文入库义务。
- **证据限制**：插件结果由父任务实际调用后回传，本代理未把插件摘要当作正文证据；仍需使用规范题录与前向引用数据库复核。

### 批次 3：Zenodo 官方版本链与 DataCite 引用关系（2026-08-12）

- **Zenodo 查询入口**：`https://zenodo.org/api/records/21330095/versions`，并逐条核验记录 API。
- **规范题名**：5 个版本均为 `TQH-C2: An Encrypted Command-and-Control Traffic Dataset Across Protocols and Encryption Layers`，作者均为 Deokjo Jeon、DongGue Park，概念 DOI 均为 `10.5281/zenodo.21330094`。

| 版本 | 发布日期 | 记录号 | 版本 DOI | 题名变化 |
| --- | --- | --- | --- | --- |
| v1.0.0 | 2026-07-13 | `21330095` | `10.5281/zenodo.21330095` | 无 |
| v1.0.1 | 2026-07-19 | `21435571` | `10.5281/zenodo.21435571` | 无 |
| v1.0.2 | 2026-07-19 | `21436858` | `10.5281/zenodo.21436858` | 无 |
| v1.1.0 | 2026-07-22 | `21484904` | `10.5281/zenodo.21484904` | 无 |
| v1.2.0 | 2026-07-24 | `21523144` | `10.5281/zenodo.21523144` | 无 |

- **重要纠正**：初始范围只列出 3 个版本 DOI；官方版本链另发现 v1.0.2 和 v1.1.0，现已纳入逐版检索。v1.0.0 的 Zenodo `publication_date` 为 2026-07-13，但记录 `created` 时间为 2026-07-18；报告将同时说明这一元数据差异。
- **DataCite 查询入口**：`https://api.datacite.org/dois/{DOI}`，分别查询概念 DOI 与 5 个版本 DOI。
- **DataCite 结果**：概念 DOI 与 5 个版本 DOI 的 `citationCount=0`、`referenceCount=0`，`relationships.citations.data=[]`、`relationships.references.data=[]`；每个版本均以 `IsVersionOf` 指向概念 DOI。
- **证据等级**：官方版本元数据与当前 DataCite 关系状态为 `E2`。
- **解释边界**：DataCite 的 0 只说明其当前关系图未登记引用，不等于不存在正文未注册 DOI 关系的使用论文；仍需逐版查 Crossref、OpenAlex、Semantic Scholar、插件和全文/Web。
- **版本归因规则**：引用版本 DOI者可归到该版本；只引概念 DOI者标为“版本不确定”，不得自动归到 v1.2.0；只写题名或 `TQH-C2` 者需用文件名、发布日期、成员 D、版本字段或代码清单判定版本。

### 批次 4：OpenAlex 逐版前向引用（2026-08-12）

- **查询式**：先以 `https://api.openalex.org/works/https://doi.org/{DOI}` 解析概念 DOI 与 5 个版本 DOI，再分别调用 `works?filter=cites:{OpenAlexID}&per-page=200`。

| 被引对象 | OpenAlex 工作号 | `cited_by_count` | 反向 `cites` 结果 |
| --- | --- | ---: | ---: |
| 概念 DOI `21330094` | `W7169722026` | 0 | 0 |
| v1.0.0 `21330095` | `W7169650382` | 0 | 0 |
| v1.0.1 `21435571` | `W7169722819` | 0 | 0 |
| v1.0.2 `21436858` | `W7169730952` | 0 | 0 |
| v1.1.0 `21484904` | `W7170037299` | 0 | 0 |
| v1.2.0 `21523144` | `W7170893341` | 0 | 0 |

- **证据等级**：`E2`。所有对象均被 OpenAlex 识别为 `dataset`，题名一致；计数和显式反向查询一致。
- **结论边界**：OpenAlex 当前没有登记前向引用作品；不排除尚未被索引或只在正文/代码中提及的数据使用。

### 批次 5：Crossref 逐版 DOI 与题名变体（2026-08-12）

- **DOI 查询式**：对概念 DOI 与 5 个版本 DOI分别执行 `query.bibliographic="{DOI}"`，取至多 1000 个候选，并在候选 `reference[].DOI` 与 `reference[].unstructured` 中再次做 DOI 字面精确匹配。
- **结果**：6 个 DOI 的精确参考文献匹配均为 0。Crossref 模糊查询的 `total-results` 不能表示命中，已明确弃用该总数。
- **题名查询式**：`TQH-C2`、`TQH C2`、`TQHC2`、完整题名；用 `query.title` 召回后再要求候选题名实际包含 `TQH-C2`。
- **结果**：四种题名查询的精确候选均为 0；未发现独立发布论文或只写题名而未写 DOI 的 Crossref 记录。
- **证据等级**：`E2`；Crossref 不索引 Zenodo 数据集本身并不异常，此处只用于论文参考文献和题名发现。

### 批次 6：Semantic Scholar 逐版 DOI 与题名补检（2026-08-12）

- **DOI 查询式**：`graph/v1/paper/DOI:{DOI}`，分别查询概念 DOI 与 5 个版本 DOI，并请求引用列表字段。
- **结果**：6 个 DOI 均返回 HTTP 404，响应为 `Paper with id DOI:{DOI} not found`，表明这些数据 DOI 当前未被 Semantic Scholar 建立论文对象。
- **题名补检**：随后查询 `TQH-C2`、`TQH C2`、`TQHC2` 与完整题名；接口返回 HTTP 429 `Too Many Requests`，不能把该批写成 0 命中。
- **证据等级**：DOI 未收录状态为 `E2`；题名结果为“未完成/限流阻塞”。后续用 Web、OpenAlex/Sider Scholar、Consensus 和 SciSpace 交叉补足。

### 批次 7：Scite 逐版补检状态（2026-08-12）

- 父任务已实际查询 v1.2.0 DOI `10.5281/zenodo.21523144` 与 v1.0.0 DOI `10.5281/zenodo.21330095`，均返回 0 且 DOI 未进入索引。
- 本代理尝试一次性补查概念 DOI 与全部 5 个版本 DOI时，Scite 返回月度 MCP 使用额度已耗尽，重置日期为 2026-09-01（UTC）。因此概念 DOI、v1.0.1、v1.0.2、v1.1.0 没有新的 Scite 查询结果；这是工具额度阻塞，不是 0 命中。
- **处理**：已核验两版保留为 `E1/E2`；其余四个对象明确标记 `Scite 未完成（额度阻塞）`，由 DataCite、OpenAlex、Crossref、Semantic Scholar、Sider Scholar、Consensus、SciSpace 和 Web/全文发现链交叉覆盖。

### 批次 8：Sider Scholar/OpenAlex 插件逐版查询（2026-08-12）

- **逐版 DOI 查询式**：`10.5281 zenodo {record_id}`，分别查询概念记录和 5 个版本；结果均为 `papers=[]`。
- **名称查询式**：`TQH-C2` 返回 100 个跨学科无关模糊词结果，没有一项题名含 TQH-C2；完整题名去掉标点后的查询返回 25 篇网络/加密流量邻近作品，全部发表于数据集公开之前。
- **分类**：DOI 精确结果为 0；名称返回项整体记作 `C 类：检索分词/语义邻近噪声`，不计入真实候选数量，不逐篇声称引用关系。
- **证据等级**：插件底层为 OpenAlex，属 `E1/E2`；与官方 OpenAlex `cites` 结果一致。

### 批次 9：Consensus 逐版与名称变体（2026-08-12）

- **合并 DOI 查询式**：概念 DOI 与 5 个版本 DOI用 `OR` 合并，返回 `results=[]`。
- **逐版 DOI 查询式**：`"10.5281/zenodo.{record_id}" TQH-C2`，概念记录与 5 个版本各执行一次，6/6 均为 `results=[]`。
- **名称查询式**：`"TQH-C2" OR "TQH C2" OR "TQHC2"`，返回 `results=[]`。
- **证据等级**：`E1`；不将空结果提升为“绝不存在”。

### 批次 10：SciSpace 全版本与逐版语义查询（2026-08-12）

- **全版本查询式**：询问哪些论文明确引用或实验使用 TQH-C2，并列出概念 DOI 与全部 5 个版本 DOI；返回 10 篇语义邻近论文，均发表于 2022–2025 年，全部早于 TQH-C2 的首次公开日。
- **逐版查询式**：对 v1.0.0、v1.0.1、v1.0.2、v1.1.0、v1.2.0、概念 DOI 分别询问 `Which scholarly papers explicitly cite or experimentally use TQH-C2 {version} with DOI {DOI}?`。
- **结果**：每次都返回 10 个语义结果，但题名集中在量子理论、程序验证或无关 Zenodo 记录；大量作品早于被查询版本，且没有题名、摘要证据显示 TQH-C2 使用。全部归为 `C 类：语义误命中`。
- **证据限制**：SciSpace 的“relevant”不等于引用；它没有返回正文引用句或匹配 DOI 的证据。不得把这些 60 条返回（含大量重复）当作 60 篇候选。

### 批次 11：Zenodo 逐版文件清单与官方 README 版本差异（2026-08-12）

- **来源**：5 个版本的 Zenodo 记录 API、临时下载的各版官方 README，以及本地 v1.2.0 README。原件/元数据均为官方来源，证据等级 `E3`（版本内容事实）。

| 版本 | 文件数/总字节 | 实质变化 | 对“实际使用版本”判定的指纹 |
| --- | --- | --- | --- |
| v1.0.0 | 8 / 52,084,512,407 | 首次公开；A/B/C 36 单元；B 旧 PCAP 约 18GB | 文件名无版本后缀；B 恶意 C2 单向、`resp_bytes=0`、`S0/OTH`；无 D |
| v1.0.1 | 8 / 52,084,512,962 | 修正 21 个单元的 `labeled.jsonl.counts.json` 计数；逐流标签、PCAP、特征、脚本不变 | 标签包 MD5 变为 `db20...`；其余核心包与 v1.0.0 相同；仍无 D |
| v1.0.2 | 8 / 52,065,104,448 | 去除陈旧容器流；总流 333,961→193,084，`unknown` 29,482→0；补全 B 特征表；PCAP 不变 | 特征包 MD5 `5de2...`、标签包 `a477...`；B 仍为旧单向采集；无 D |
| v1.1.0 | 8 / 38,083,782,408 | 修复杀伤链并重新采集 12 个 B 单元；B 变为 324/324 双向 C2，B PCAP 缩至约 4GB；A/C 沿用 v1.0.2 | 文件名 `_v110`；B PCAP MD5 `0a5a...`；无 D |
| v1.2.0 | 11 / 39,909,292,397 | 在 v1.1.0 的 A/B/C 基础上新增 D（Merlin HTTP/2-over-TLS/TCP）12 单元 | 出现 `TQH-C2_pcap_D_merlin_h2.zip`、`features_D`、`labels_D`；A/B/C 包与 v1.1.0 字节相同 |

- **元数据/README 不一致**：v1.0.0 记录的 `publication_date=2026-07-13`，README changelog 写“2026-07-18 首次公开”；v1.1.0 记录日期为 2026-07-22，README changelog 写 2026-07-21。报告以 Zenodo 记录发布日期为规范字段，同时保留 README 自述日期。
- **引用块错误风险**：v1.1.0 README 与本地 v1.2.0 README 虽标注相应版本，但引用块仍给出 v1.0.0 DOI `10.5281/zenodo.21330095`。因此，论文只引用 `21330095` 不足以确认其实际使用 v1.0.0；必须结合下载时间、D 成员、B 方向性、文件名或校验和判版。
- **重要结论**：版本无法确认时不能根据引用 DOI机械归因；尤其 `21330095` 可能来自后续 README 的错误引用模板。实验审计表将把“被引版本”和“实际所用版本”分开。

## 候选分类台账

| 候选 | 稳定标识符 | 分类 | 证据等级 | 全文 | 理由 | Zotero |
| --- | --- | --- | --- | --- | --- | --- |
| SciSpace 的 10 篇 2022–2025 语义邻近作品 | 见批次 2 | C | E1 | 不适用 | 全部早于 TQH-C2 公开，不可能形成前向引用或实际使用 | 不导入 |

## A 类实验使用矩阵

| 论文 | 数据成员 | 任务 | 样本单位 | 字段 | 切分 | 泄漏防护 | 模型/基线 | 指标/结果 | 代码 | 全部/抽样 | 与本课题关系 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

## 新增综合：安全任务机会矩阵合同

- **评估对象**：封闭集分类、开放集未知攻击、跨版本/跨环境泛化、持续学习与概念漂移、机器遗忘、投毒/后门恢复、选择性预测/拒识、概率校准与告警预算、流式早期检测、攻击链阶段识别/溯源、异常解释、主动学习/少样本、隐私审计（以及用户列出的全部任务，不合并漏项）。
- **每项必填**：数据可构造性、强基线、指标、既有分数是否饱和、关键缺陷、可创新方向、最小可证伪实验。
- **证据档位**：
  - `D1 可直接构造`：现有原件有可观测量、标签/目标和合法切分键；仍需真实实验。
  - `D2 弱构造`：需代理标签、人工标注、合成扰动或额外假设；只能作为候选，不能写成数据集原生支持。
  - `D3 当前不支持`：缺少目标标签、因果时间、干预、身份或足够独立事件，无法用现有制品形成可信实验。
- **设计选择**：推荐采用“证据门禁矩阵”；已向父任务请求批准。获批前继续只读事实核验，不提前选前三或写创新裁决。
- **硬边界**：没有引用论文不构成研究空白证据；官方 README 的建议用途不等于任务有效；本课题内部高分必须区分随机/组级/跨域、历史版本和捷径字段预算。

## 无法获取全文清单

| 题名 | 作者/年份 | DOI/URL | 已尝试入口 | 阻塞 | 建议文件名 |
| --- | --- | --- | --- | --- | --- |
| 暂无 |  |  |  |  |  |

## 下一动作

1. 用 `rg` 检索 `TQH-C2`、`TQHC2`、`TQH C2`、全部 DOI 和 Zenodo 记录号。
2. 盘点 `raw/`、`wiki/`、已有综述、索引与 Zotero。
3. 核验 Zenodo/DataCite 元数据，确定规范题名、作者、版本关系和是否存在伴随论文。

## 2026-08-12 中断恢复检查点

> 状态：`CHECKPOINT_SAVED`。用户即将中断会话，已停止所有新增检索。以下是可恢复状态，不代表任务完成。

### 完成度与数量

- 总完成度：约 `65%`。
- 五版官方链与差异审计：约 `90%`。五个版本均已完成 DOI/记录号/日期/文件清单/主变更核验。
- 精确候选数：`0`；`A=0`、`B=0`。
- `C` 类语义噪声：约 `195` 个原始返回行，含重复，不能当作唯一论文数。它们均在候选纳入前由发表日期、DOI/题名不匹配或完全无关主题排除。
- 取得合法全文：`0`。原因是没有 A/B 类作品，而非可疑论文全文获取失败。
- 任务机会矩阵：约 `25%`；13 项必评任务与 `D1/D2/D3` 证据门禁已冻结，正式逐项表和前三推荐未写完。

### 五版核验状态

| 版本 | 记录号 | DOI | 官方发布日 | 引用源完成度 | 文件/模式完成度 |
| --- | --- | --- | --- | --- | --- |
| v1.0.0 | `21330095` | `10.5281/zenodo.21330095` | 2026-07-13 | 主要源已查；Scite 已查为 0 | 约 90% |
| v1.0.1 | `21435571` | `10.5281/zenodo.21435571` | 2026-07-19 | 主要源已查；Scite 额度阻塞 | 约 90% |
| v1.0.2 | `21436858` | `10.5281/zenodo.21436858` | 2026-07-19 | 主要源已查；Scite 额度阻塞 | 约 90% |
| v1.1.0 | `21484904` | `10.5281/zenodo.21484904` | 2026-07-22 | 主要源已查；Scite 额度阻塞 | 约 90% |
| v1.2.0 | `21523144` | `10.5281/zenodo.21523144` | 2026-07-24 | 主要源已查；Scite 已查为 0 | 约 90% |
| 概念记录 | `21330094` | `10.5281/zenodo.21330094` | 随版本演进 | 主要源已查；Scite 额度阻塞 | 不适用 |

五版差异制品的未完成项：将已核验的标签计数、字段模式、A/B/C/D 包含关系、关键校验和、README/元数据日期冲突与错引 DOI 风险整合进独立表。

### 各源最后状态

- Zenodo/DataCite：概念 DOI 与 5 个版本均已核验；DataCite 当前 `citationCount=0`、`referenceCount=0`。
- OpenAlex：概念 DOI 和 5 个版本都有数据集工作号；`cited_by_count=0`，显式 `cites:` 反向查询也为 0。
- Crossref：6 个 DOI 的参考文献精确字面命中为 0；4 组题名变体没有精确题名候选。
- Semantic Scholar：6 个 DOI 均返回 404 未收录；题名批次后续触发 HTTP 429，该批不能写成 0。
- Scite：v1.0.0 和 v1.2.0 已查为 0 且 DOI 未入索引；概念 DOI、v1.0.1、v1.0.2、v1.1.0 因月度额度耗尽而未完成。
- Sider Scholar：6 个记录号逐个查询均 `papers=[]`；名称/完整题名返回为分词或语义噪声。
- Consensus：六 DOI 合并、逐个 DOI 和名称变体均 `results=[]`。
- SciSpace：全版本和 6 个对象逐个检索只返回早于数据集发布或主题无关的语义结果，全部批次排除为 C 类噪声。
- Web/Google 可达替代：精确题名与各版 DOI 搜索只返回 Zenodo 自身或无关项；作者+题名只发现 Zenodo/ORCID 入口，未发现独立论文。
- DBLP：API 返回 HTTP 500，不能声称完成或 0；网页精确搜索未见候选。
- GitHub：公开代码 API 因匿名限额失败；网页精确搜索只见无关摘要，外部复现/实验使用仍未核验。

### 未关闭疑点与边界

1. 尚未把 v1.2.0 各成员实际标签分布、Parquet/JSONL 模式和 D 标签包的具体文件差异固化为独立制品。
2. 尚未完成作者 ORCID 作品列表的精确交叉核验与 OpenCitations 补检；这两项是恢复后可选的第二轮收尾，不得在当前检查点冒充已查。
3. 暂无 A/B 类论文，因此没有可下载全文、没有可建 `wiki/papers/` 全文笔记；此状态仍需在最终检索收敛后重新确认。
4. Zotero 只有键 `AHY833JP`，元数据标注 v1.0.1 但 DOI 是 v1.0.0 `21330095`，无 PDF 子项。尚未写入新条目，以避免在版本引用规则未裁决前制造重复。
5. 尚未生成主报告、版本差异独立制品、wiki 资源笔记或索引更新；未修改实验源码、RWKV 总控、恢复卡或候选登记册。

### 精确阻塞、唯一恢复动作与交付路径

- 阻塞：Semantic Scholar HTTP 429；Scite 额度耗尽至 2026-09-01 UTC；DBLP HTTP 500；GitHub 匿名 API 限流。
- **唯一下一动作**：恢复后先完整重读本文件与 `task_plan.md`，在不发起新查询的前提下，先写 `.Codex/docs/RWKV/2026-08-12-TQH-C2引用论文审计/TQH-C2五版差异矩阵.md`。
- 预计恢复后剩余时间：`60–90 分钟`。
- 最终报告路径：`.Codex/docs/RWKV/2026-08-12-TQH-C2引用论文查全审计.md`，当前尚未生成。

## 2026-08-12 恢复执行日志

- 已完整重读 `task_plan.md` 与本 `notes.md`，并按唯一下一动作开始固化五版差异制品；本批未发起网络查询。
- 本地 v1.2.0 实测标签计数：A=`benign 83,881`、`benign_external 230`、`malicious_c2 12,038`；B=`benign 21,472`、`malicious_c2 324`；C=`benign 9,378`、`benign_external 230`、`malicious_c2 12,804`、`malicious_recon 880`；D=`benign 9,564`、`malicious_c2 1,964`。合计 152,765 条流记录，实际不含 `malicious_lateral` 或 `unknown`。
- 标签包结构实测：A/B/C 包含 36 份 `labeled.jsonl`、Zeek 日志、计数、门禁与 manifest；D 包只有 12 份 `labeled.jsonl` 和 12 份 `manifest.json`，没有 `conn.log`、计数或门禁文件。
- 首次 Parquet 模式检查命令从 `thesis/experiments/llm_probe/` 使用了错误的仓库相对路径，且 `uv` 默认缓存目录受沙箱限制；命令在读取 Parquet 前失败，未修改数据、文档或实验代码。下一次使用绝对路径和 `/private/tmp` 专用 `UV_CACHE_DIR`。
- Parquet 重试成功：A/B/C/D 聚合表分别为 96,149 / 21,796 / 23,292 / 11,528 行，全部为相同 27 列模式。五版差异制品已生成于 `TQH-C2五版差异矩阵.md`，并通过 `git diff --check`、非空、关键词与占位符检查。
- 证据门禁任务机会矩阵已生成于 `TQH-C2任务机会矩阵.md`，含 14 项任务的 D1/D2/D3 裁决、强基线、指标、饱和度、缺陷、可创新方向、最小可证伪实验与前三推荐；结构检查得到 14 个逐项合同，无占位符。

### 批次 12：OpenCitations、ORCID 与 DBLP 第二轮收尾（2026-08-12）

- **OpenCitations COCI**：对概念 DOI 和 5 个版本 DOI 逐个调用 `coci/api/v1/citations/{DOI}`。首次沙箱请求因 DNS 返回 HTTP `000`；受控网络重试先返回 301，跟随 HTTPS 重定向后 6/6 均为 HTTP 200、引文数组长度 0。只将最后 HTTP 200 结果记为索引当前为 0，`000` 和 301 仅为请求过程状态。
- **作者 ORCID**：Deokjo Jeon（`0000-0002-0343-3384`）公开 works 接口返回 4 个作品汇总；精确题名与六个 DOI 交叉筛选命中 0。这只说明当前作者 ORCID 作品列表没有 TQH-C2 记录或伴随论文。
- **DBLP**：首次旧检查点为 HTTP 500；本次重试 `search/publ/api?q=TQH-C2&format=json&h=100` 返回 HTTP 200，`total=0`。因此 DBLP 阻塞已解除，当前精确检索为 0。
- **第二轮裁决**：OpenCitations、ORCID 和 DBLP 没有新增精确候选，也没有新增 A 类。与第一轮的 DataCite/OpenAlex/Crossref/插件/Web 相独立，满足“连续两轮无新增 A”的当前停止条件。
- **仍然阻塞**：Semantic Scholar 题名查询 HTTP 429；Scite 的概念 DOI、v1.0.1、v1.0.2、v1.1.0 因月度额度耗尽；GitHub 匿名代码 API 限流。这三项仍不得写为 0。

### Zotero 更新裁决（2026-08-12）

- 本地 Zotero 只有数据集条目 `AHY833JP`，其 `Extra` 标 v1.0.1，DOI 却为 v1.0.0 `10.5281/zenodo.21330095`。
- 试图在原条目上最小更新为 v1.2.0 DOI 和概念 DOI 说明时，写工具转向云端用户库并返回 HTTP 404 `Item does not exist`。切换到本地用户库后再试仍返回同一 404。
- **裁决**：不新建第二个数据集条目，避免制造重复；当前状态明确记为“本地条目可读，云端/本地写上下文不一致导致写入受阻”。不声称 Zotero 已更新。

## 扩展任务：相似数据集与可迁移方法

- **新增范围**：五条轴分别为加密 C2/恶意 TLS 或 QUIC 检测、跨捕获/跨网络/跨数据集泛化、跨域校准/告警预算/选择性拒识、流前缀早识别、开放集未知恶意流量。
- **固定输出字段**：每篇必须记录相似类型（数据集相似 / 任务方法相似 / 两者）、数据、分割、特征、强基线、指标、缺陷、可迁移机制、TQH-C2 最小实验映射、原件/wiki/Zotero 状态。
- **落盘频率**：每 3–4 篇全文形成一个批次检查点，不等所有论文完成后回忆补写。
- **论断边界**：直接引用 A=0 不能支持“没有相似数据/方法”或“研究空白”；相似方法必须以全文实验为证据。

### 相似数据与方法批次 1：4 篇本地全文（2026-08-12）

本批已重新从本地 PDF 提取文本并回到对应数据/实验段，不只复用 wiki 摘要。

| 论文 | 相似类型 | 数据/划分/特征 | 强基线与指标 | 缺陷 | 可迁移机制 | TQH-C2 最小实验 | 入库状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Anderson & McGrew 2016, *Identifying Encrypted Malware Traffic with Contextual Flow Data* | 数据集与任务均相似：TLS 加密恶意/良性流，但非受控 C2 跨协议网格 | 恶意商业沙箱 13,542 条完整上下文 TLS 流，良性企业网 42,927 条；十折交叉验证，另用同企业四周后 988,105 条 TLS 流作时间外核验；包长/间隔、字节分布、TLS、DNS/HTTP 上下文 | L1 逻辑回归、高斯核 SVM、特征组消融；低误报阈值准确率和人工告警复核 | 恶意/良性来源异质；时间外仍是同企业；上下文覆盖有限 | 将“同主体相邻流上下文”与低告警工作点结合 | 在不使用 IP 输入的前提下，仅用同 capture 时间窗汇总上下文，对比单流 HGB 与上下文逻辑回归；在 C 上报固定误报下召回 | PDF、wiki、Zotero `SRXPRRXP` 已闭合 |
| Novo & Morla 2020, *Flow-based Detection and Proxy-based Evasion of Encrypted Malware C2 Traffic* | 数据集/任务相似：恶意 TLS C2 逐流检测；不是多协议受控域 | 508 个 PCAP、20,747 条 TLS 流，7,672 恶意/13,075 良性；下采样平衡后随机 20% 测试；86 个 TStat 流特征 | 三层全连接检测器，FGSM 特征空间/受约束/真实 PCAP 代理攻击、迭代对抗训练；准确率、恶意误分率 | 流随机划分可泄漏同 PCAP/感染事件；良性标签由未命中黑名单推得；人为平衡 | 将对抗证据拆为特征空间上界、PCAP 可实现攻击与代价测量 | 在 B/D 各两个开发 capture 上实现只增包/字节/时延的因果扰动，对比表格 FGSM 与重物化 PCAP，报攻击成功率、C 召回、误报和带宽/延迟代价 | PDF、wiki、Zotero `WGV3LGJJ` 已闭合 |
| Fu et al. 2024, *Flow Interaction Graph Analysis: Unknown Encrypted Malicious Traffic Detection* | 任务/方法相似：未知加密恶意流量与实时告警；数据结构为交互图，非 TQH-C2 单流表 | MAWI 2020-01–06 背景，80 组生成/重放攻击+12 公开数据，共 92 组；主实验前 75% 时间为无恶意基线，四折轮换调参/测试；长短流与交互图 | Jaqen、FlowLens、Whisper、Kitsune、DeepLog；AUC、F1、吞吐、检测时延、内存 | 攻击与背景来源异质；45 秒主实验很短；“未知”不是受控协议迁移 | 将检测、未知性、时延、吞吐与内存放入同一证据矩阵；用流交互而非单流分数 | 在每个 capture 内构建去 IP 节点身份的时间窗交互统计，对比单流 HGB 和简单图异常基线；留出 C，并报吞吐/时延 | PDF、wiki、Zotero `BGRA3ZRR` 已闭合 |
| Cantone et al. 2024, *Cross-Dataset Generalization of NIDS* | 任务/协议相似：整数据集域外泛化；数据为 CIC/LycoS NIDS，不是加密 C2 | 四个数据集、二元攻击/良性映射；域内 80:20 随机分，跨域使用完整数据集训练→另一完整数据集测试 | 四种传统机器学习分类器；MCC 为主，域内平均 94.63%、跨数据平均 29.35% | 二元标签交集丢失攻击类型语义；数据集生成与特征差异混杂 | 严格分开域内与整域外评价，报泛化落差而非 pooled 分数 | 冻结 A+B→C、A+B+D→C 与 B↔D，统一 7 字段/强基线/预算，报域内—域外差值、MCC、宏 F1、恶意召回与误报 | PDF、wiki 已闭合；Zotero 键需在最终表补核 |

**批次 1 结论**：Novo 与 Anderson 最接近 TQH-C2 的“加密恶意/C2 逐流检测”数据和任务；Cantone 只是严格跨数据协议相似；HyperVision 是未知、告警和系统评价方法相似。四篇都不能代替 TQH-C2 的 A/B/D→C 真实实验。

### 相似数据与方法批次 2：校准与选择性拒识 3 篇全文（2026-08-12）

| 论文 | 相似类型 | 数据/划分/特征 | 强基线与指标 | 缺陷 | 可迁移机制 | TQH-C2 最小实验 | 入库状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Guo et al. 2017, *On Calibration of Modern Neural Networks* | 任务/方法相似；数据不相似 | CIFAR-10/100、ImageNet、SVHN 等图像与文本任务；独立验证集拟合事后校准器，默认训练/验证/测试同分布 | 直方图分箱、保序回归、BBQ、Platt、矩阵/向量/温度缩放；ECE、NLL、Brier/可靠性图 | ECE 依赖分箱；原实验是同分布，不能保证跨 C | 在冻结校准组上拟合单参数温度，不改变类别预测 | 对 HGB/XGBoost/深度候选用独立 capture 拟合 Platt/保序/温度，在未见 C 比较 NLL、Brier、逐组 ECE 与同告警预算召回 | PDF、wiki、Zotero `Y8NQEYKT` 已闭合 |
| Ovadia et al. 2019, *Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift* | 任务/方法相似；数据不相似 | MNIST/CIFAR/ImageNet 等；从连续增强的合成协变量偏移到完全 OOD；没有安全流量字段 | 原始模型、温度缩放、MC-dropout、模型集成、贝叶斯近似；准确率、Brier、可靠性/熵 | 合成图像偏移不等同真实网络偏移；无告警预算 | 把校准评价扩展到递增偏移和完全域外，并用集成作不确定性强基线 | 冻结 A→B/D→C 偏移阶梯，比较单模型事后校准与同预算集成；若域内校准在 C 上失效，不得沿用阈值 | PDF、wiki、Zotero `MTKK55LQ` 已闭合 |
| Geifman & El-Yaniv 2019, *SelectiveNet* | 任务/方法相似；数据不相似 | SVHN、CIFAR-10、Cats vs. Dogs 和一个回归数据；为指定覆盖率训练联合预测/选择头，独立验证集校准覆盖阈值 | 最大软最大响应、MC-dropout；选择风险、覆盖率、风险—覆盖曲线 | 同分布图像任务；不报最差组或跨域风险 | 目标覆盖率的端到端拒识和独立覆盖校准 | 对未见 C 预注册 50/75/90% 覆盖率，对比概率/边际/集成分歧；低风险若需拒绝几乎全部 C 即否决 | PMLR PDF 已入 raw，wiki 笔记已建；Zotero `CCBBGX8E` 已导入（未重复附 PDF） |

**批次 2 结论**：Guo 只能支持同分布事后校准基线；Ovadia 直接否决“验证集校准可自动迁移到偏移域”；SelectiveNet 给出风险—覆盖基线，但跨 C 的组风险是 TQH-C2 必须新增的证据。

## 2026-08-12 最新可恢复检查点

> 状态：`CHECKPOINT_SAVED`。已停止新增检索；以下是精确恢复状态，不代表整个扩展任务已经交付。

### 完成度与数量

- 代理映射：`/root/tqhc2_citation_literature_sol_max` → `gpt-5.6-sol` → `effort=max`。
- 总完成度约 `88%`；直接引用查全 `100%`、五版差异 `100%`、任务机会矩阵 `100%`、主报告初稿 `90%`、相似数据/方法扩展第一层 `7` 篇全文完成，独立扩展尚未接入。
- 直接引用精确候选：`A=0`、`B=0`；A/B 全文 `0`。C 类为约 `195` 个原始语义返回行，含跨查询与跨插件重复，不能报作唯一论文数。
- 相似任务/方法全文：`7` 篇，分别为 Anderson 2016、Novo 2020、Fu/HyperVision 2024、Cantone 2024、Guo 2017、Ovadia 2019、Geifman/SelectiveNet 2019；均已回到全文核验数据、切分、特征、强基线、指标、缺陷、可迁移机制与 TQH-C2 最小实验。
- 当前本代理范围内缺失全文：`0`。直接链无 A/B 候选；已纳入 7 篇均有合法全文。独立相似数据集扩展若遇受限全文，必须写入其逐项人工下载清单。

### 已落盘制品

- 主报告初稿：`.Codex/docs/RWKV/2026-08-12-TQH-C2引用论文查全审计.md`（228 行）。
- 五版差异：`.Codex/docs/RWKV/2026-08-12-TQH-C2引用论文审计/TQH-C2五版差异矩阵.md`（140 行）。
- 任务机会矩阵：`.Codex/docs/RWKV/2026-08-12-TQH-C2引用论文审计/TQH-C2任务机会矩阵.md`（236 行）。
- 长期知识条目：`wiki/resources/TQH-C2-Zenodo数据集版本与外部使用审计.md`，并已接入 `wiki/resources/INDEX.md`。
- 新增全文原件：`raw/papers/methodology/2019-Geifman-SelectiveNet.pdf`；SHA-256 为 `121c044e3fc396f0b274a1bdbbddd1f73f016814ee76a7aed8a6898fb51388f9`。
- 新增全文笔记与索引：`wiki/papers/methodology/Geifman2019-SelectiveNet选择性预测.md` 与 `wiki/papers/methodology/INDEX.md`。
- Zotero：SelectiveNet `CCBBGX8E`、Cantone `ZVJCXA5N`；其余五篇的既有键已在批次表与主报告记录。

### 各外部源最后状态

- DataCite、OpenAlex、Crossref、OpenCitations、ORCID、DBLP：概念 DOI 与五版/题名链已完成，未新增精确候选。
- Semantic Scholar：六 DOI 均 404 未建对象；题名批次 HTTP 429，不能记作 0。
- Scite：v1.0.0、v1.2.0 为 0 且未入索引；概念 DOI 与 v1.0.1/v1.0.2/v1.1.0 因月度额度阻塞，不能记作 0。
- Sider、Consensus：精确 DOI/名称查询无候选；SciSpace 返回语义噪声，已按证据逐批排除。
- GitHub：匿名代码 API 限流；网页精确搜索未形成可核验外部使用，API 状态仍为阻塞。

### 未完成项与唯一恢复动作

1. 独立代理 `/root/tqhc2_analog_datasets_literature_sol_max` 正在负责 USTC-TFC2016、CESNET-TLS-Year22、CESNET-QUIC22、H23Q、CIRA-CIC-DoHBrw-2020、CIC-AndMal2017 等数据集的六维评分，以及流前缀、开放集和受限全文人工下载清单。本代理已与其去重，没有重复分析前述 7 篇。
2. 主报告初稿尚未接入该独立制品，尚未执行最终跨文件映射、引用链接与人工下载清单验收。
3. **唯一恢复动作**：先重读本检查点，再只读检查 `.Codex/docs/RWKV/2026-08-12-TQH-C2相似数据集与可迁移任务文献综述/` 的最新状态；只接入已由全文、raw/wiki/Zotero 闭合的条目，然后运行最终 `git diff --check`。在此之前不发新查询。

## 2026-08-12 最终整合记录

### 独立相似数据综述接入裁决

- 已重读独立目录的 `task_plan.md`、`notes.md` 与 `缺失全文与人工下载清单.md`。
- 额外全文核验检查点为 4 篇：CBSeq、Lichy、Cruz 开放集、H23Q。其 PDF 与既有 wiki 笔记均存在；但独立代理明确回报“最终闭合条目=0、最终六维评分=0”，所以主报告只写已核验事实和边界，不给虚构相似度分数或最终排名。
- 流前缀候选 ECHO、Early Online Classification、TFFlow 尚未完成全文证据卡；FlowPic、XeNIDS、Sweet Danger、TCBench、CESNET-TLS-Year22、CESNET-QUIC22、TLS reject-option、USTC-TFC2016、CIC-AndMal2017、CIRA-CIC-DoHBrw-2020 也仍是待复用或待访问审计候选，未进入全文结论。
- 人工下载清单的已确认阻塞为 0；仍待合法访问审计的 4 项是 USTC-TFC2016 PDF、CESNET-QUIC22 官方 PDF、CIC-AndMal2017 原论文、CIRA-CIC-DoHBrw-2020 原论文。未把“尚未下载”误写成“付费墙”。

### 用户最终候选裁决

- 候选不要求新场景；已有论文覆盖同一任务/场景，不构成否决。
- 第一轨“同协议直接改进”：冻结数据版本、划分、字段、训练/推理预算和指标；若强基线仍有可重复余量，则允许直接改进。
- 第二轨“更严格稳健性验证”：在完整 capture/成员留出、跨 C、最差组、固定告警预算、风险—覆盖或因果前缀下验证既有结论；更严格评价本身不等于算法原创。
- 领域对抗、组分布鲁棒优化、上下文/图交互、温度缩放、选择性拒识和流前缀等已有机制只能作为来源与强基线。新方法必须绑定可识别新增机制、相同预算强基线、独立机制消融和预注册失败门槛。
- 当前前三排序不变：跨成员泛化最适合论文章级贡献；跨域校准/告警预算/拒识第二；B/D 流前缀第三。排序依据是数据门禁与已观测余量，不是场景是否第一次出现。

### 最终交付状态

- 主报告已整合直接引用、五版差异、7 篇最终闭合相似方法全文、4 篇额外全文核验检查点、未闭合候选边界、两轨机会和原创性门禁。
- 本任务到此完成；未来重跑受阻引用源或继续独立相似数据六维综述属于后续扩展，不是本报告的隐含已完成项。
