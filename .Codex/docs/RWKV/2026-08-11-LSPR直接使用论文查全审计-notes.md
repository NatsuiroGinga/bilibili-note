# LSPR 直接使用论文查全审计工作笔记

## 审计元数据

- 检索日期：2026-08-11
- 路线：`RESEARCH_ROUTE=RWKV`
- 时间范围：数据库建库起始至 2026-08-11
- 数据集范围：LSPR23、LSPR24、LSPR25 及 Locked Shields Packet Repository／Locked Shields flow dataset 等别名
- 工作边界：只做文献、原件、结构化笔记、索引与 Zotero；不触碰实验代码、远端物化和最终测试

## 已知本地候选

| 研究 | 初始分类 | 全文 | 本地原件 | Zotero |
| --- | --- | --- | --- | --- |
| Dijk 等 2024，LSPR23 发布与随机森林复现 | A：直接模型实验 | 已核验，2026-08-11 由用户提供 | `raw/papers/datasets/1-s2.0-S2214212624001492-main.pdf` | `CDDWA2UR`，本地链接附件 `NAPDXPQS` |
| Dijk 等 2025，LSPR24 发布论文 | A-R：直接发布统计，无模型评价 | 已核验 | `raw/papers/datasets/2025_Meier_LSPR24_Blue-Team-Automation.pdf` | `XXQ64ZGX` |
| Leoste 2025，LSPR23→LSPR24 | A | 已核验 | `raw/papers/datasets/LSPR24/2025_Leoste_Comparative_Analysis_ML_DL_LSPR23_LSPR24.pdf` | `M8EZZ9S9` |
| Dijk 等 2026，LSPR23／24／25 序列构造 | A | 已核验 | `raw/papers/datasets/LSPR24/ssrn-6597680.pdf` | `U4ZMBMEK` |
| Di Gennaro 等 2026，KRONOS-SDN 未知攻击检测 | B：只引用 LSPR23 | 已核验 | `raw/papers/datasets/LSPR24/2026_DiGennaro_Hierarchical_Hybrid_SDN_IDS.pdf` | `VRA8LK86`，PDF 子附件 `DCRYX3U8` |

## 查询记录

每完成一组查询立即补充：来源、精确查询式、返回数、人工筛选数、去重后新增 A／B 数、C 类噪声、不可访问项与下一步。

### 检索词矩阵

- 年度名：`LSPR23`、`LSPR24`、`LSPR25`、`LSPR 23/24/25`、`LSPR-23/24/25`。
- 官方全称与自然语言别名：`Locked Shields Partners Run`、`Locked Shields Packet Repository`、`Locked Shields flow dataset`、`Locked Shields dataset`、`Locked Shields network flows`。
- 文件和版本别名：`LS23PR`、`ls23pr_flows`、`lspr24_v2.parquet`、三个 Zenodo DOI。
- 题名与 DOI：LSPR23 正式题名／`10.1016/j.jisa.2024.103847`；LSPR24 发布论文题名／`10.23919/CyCon65856.2025.11103720`；序列构造题名／`10.2139/ssrn.6597680`。
- 作者链：Allard Dijk、Emre Halisdemir、Cosimo Melella、Alari Schu、Mauno Pihelgas、Roland Meier、Risto Vaarandi、Johan Valdemar Leoste。

### 可计数的结构化查询

下表的“返回行”是每次查询返回的记录行，跨查询有大量重复；不能把它当成唯一论文数。网页搜索和作者页没有稳定总数，另作人工核验，不混入返回行合计。

| 来源 | 查询与返回 | 去重后新增 A | 去重后新增 B | 说明 |
| --- | --- | ---: | ---: | --- |
| Zenodo／DataCite | 三个数据 DOI 与 related identifiers，共 3 个主记录 | 0 | 0 | 数据记录不是论文；LSPR25 记录反向指向序列构造伴随论文。三个数据记录的 Zenodo 文献引用计数均为 0，不能据此断言无人使用。 |
| Crossref | `LSPR23` 1、`LSPR24` 0、`LSPR25` 0；序列构造精确题名 1 | 0 | 0 | 仅找回 LSPR23 正式论文和 SSRN DOI；截至检索日没有找回声称的 *Computer Networks* 正式 DOI。 |
| OpenAlex | 全文检索 `LSPR23` 5、`LSPR24` 5、`LSPR25` 3、正式短语 2；LSPR23 原论文被引 5；LSPR24 发布论文被引 1，共 21 个查询行 | 1 | 3 | 新增 Dijk 2026；引用链带出两篇只引用原论文及一篇只引用 LSPR24 发布论文。另有一条建筑火灾综述的疑似错误引文边。 |
| Semantic Scholar 官方接口 | 精确题名与 DOI | 0 | 0 | HTTP 429，未形成可用结果；由 OpenAlex、Scite、Sider Scholar、DBLP 和正式载体交叉替代。 |
| Scite | `"LSPR23" OR "LSPR24" OR "LSPR25"` 共 3 条 | 0 | 0 | Dijk 2024、Dijk 2026 和 1 条局域表面等离激元误命中；没有新增 A／B。Dijk 2024 当时显示非开放获取，后由用户全文消除阻塞。 |
| Consensus | 分别询问直接使用 LSPR23／24／25 的论文；每次总数显示 20、返回前 10，共 30 个查询行 | 0 | 0 | 只稳定找回 Dijk 2024；遗漏本地已知 Leoste 2025 和 Dijk 2026，不能单独承担查全。 |
| Sider Scholar 学术搜索 | 精确 `LSPR23` 1、`LSPR24` 0、`LSPR25` 0、正式短语／文件别名 0 | 0 | 1 | 唯一新增是 Di Gennaro 2026；全文确认只在相关工作引用 LSPR23，实验用 KRONOS-SDN。 |
| SciSpace | 4 个自然语言直接使用查询和 3 个精确年度查询，每次 10，共 70 个查询行 | 0 | 0 | 未找回 4 篇已知 A；主要返回旧式 IDS、私有 Locked Shields 数据和局域表面等离激元噪声。 |

以上结构化查询共有至少 **130 个查询结果行**。规范化题名、DOI、作者、年份和版本后，19 个记录进入人工纳排复核：A 类 4、B 类 5、C 类／文档类型排除 10。网页搜索、出版社 cited-by、大学仓储、作者页和会议库用于反向核查，没有把不稳定的网页“约多少条”混入 130。

### 网页、载体、作者链与引用链

| 来源 | 精确入口／查询 | 结果 |
| --- | --- | --- |
| ScienceDirect | LSPR23 正式页面的 cited-by | 正式页面列出 4 个引用者：Dijk 2025 为 A-R；Di Gennaro 2026、Faiaz 等 2024、Staněk 等 2025 为 B。 |
| DBLP、IEEE、ACM、Springer | 年度缩写、题名、DOI、作者组合 | DBLP 只确认 Dijk 2024 正式题录；IEEE 找回 Dijk 2025 与两篇 B；ACM 找回 NSL-KDD B；没有新增 A。 |
| TalTech 仓储 | `LSPR23`、`LSPR24`、作者与学位论文下载页 | 找回 Leoste 2025 全文；排除同仓储目录拼接造成的无关论文误命中；没有第二篇 LSPR 学位论文。 |
| SSRN、arXiv、Research Square | 年度缩写、题名、作者 | SSRN 只找回 Dijk 2026；arXiv／Research Square 无新增 A。 |
| CEUR-WS | LSPR23 与 cited-by 新文 | 新增 Di Gennaro 2026，全文确认为 B。 |
| 作者主页／机构页 | Dijk、Meier、Pihelgas、Vaarandi、Leoste | 找回 4 篇已知 A 及旧私有 Locked Shields 先行工作；没有新增公开 LSPR23／24／25 直接使用论文。 |
| 文件名／数据 DOI 搜索 | `ls23pr_flows`、`lspr24_v2.parquet`、三个数据 DOI | 只回到官方记录、4 篇 A 和重复聚合页；没有额外下游实验。 |

### 插件增量记录

| 插件 | 查询数／命中 | 去重后新增 A | 去重后新增 B | 不可访问或限制 |
| --- | ---: | ---: | ---: | --- |
| Consensus | 3 次，每次返回前 10 | 0 | 0 | 只提供候选摘要；未把摘要当全文证据。 |
| Scite | 1 次宽检索 3 条，另查 Dijk 2024 可用性 | 0 | 0 | Dijk 2024 当时只有付费获取提示；用户随后提供正式全文。 |
| Sider Scholar | 7 组精确／别名查询 | 0 | 1 | 新增 Di Gennaro 2026，已回到 CEUR 官方全文核验。 |
| SciSpace | 7 次，每次 10 | 0 | 0 | 语义噪声高，且漏掉已知 A；仅用于召回补充。 |

插件的共同结论是：它们能扩展相似论文和 B／C 类召回，但对这个低频、新近、跨载体数据集族的查全明显不够；最终分类全部回到正式全文、正式题录、DOI、作者页或官方仓储。

## 人工纳排台账

### A 类：直接读取 LSPR 数据

1. Dijk 等 2024，LSPR23 数据发布、Suricata 评价和随机森林复现。
2. Dijk 等 2025，LSPR24 发布与全量描述性分析；无训练模型，标记为 A-R。
3. Leoste 2025，LSPR23 训练、LSPR24 零重训测试。
4. Dijk 等 2026，LSPR23／24／25 序列构造、同年和跨年评价。

### B 类：只引用或介绍

1. Faiaz、Mitra、Prangon 2024，*Intrusion Detection Using Convolutional Neural Network: A Color Mapping Approach on NSL-KDD Dataset*，DOI `10.1145/3704522.3704541`；实验仅用 NSL-KDD。
2. Staněk、Klaban、Coufalíková 2025，*Explainable Artificial Intelligence: State of the Art and Beyond*，DOI `10.1109/ICMT65201.2025.11061287`；综述性引用，无 LSPR 实验。
3. Di Gennaro 等 2026，*A Hierarchical Hybrid Deep Learning Framework for Unknown Attack Detection in SDN Networks*；全文仅把 LSPR23 列为传统基准，实验只用 KRONOS-SDN。
4. Devi Priya、Sethuraman、Khan 2025，*Blockchain-based Deep Learning Models for Intrusion Detection in Industrial Control Systems: Frameworks and Open Issues*，DOI `10.1016/j.jnca.2025.104286`；综述列举 LSPR23，无 LSPR 实验。
5. Andrade 2026，*Retomando a iniciativa: inteligência prospectiva e capacidade ofensiva para a proatividade no ciberespaço*，DOI `10.5902/2357797595736`；只在战略讨论中引用 Dijk 2025，无数据处理。

### C 类：排除

- Känzig 等 2019 和 Gehri 等 2023 确实使用 Locked Shields 流量，但数据来自公开 LSPR23 之前的私有年度／私有采集，不能冒充 LSPR23／24／25。
- Halisdemir 等 2022 的数据质量方案是 LSPR23 的先行方法来源，发表时公开 LSPR23 尚不存在。
- 以 `LSPR` 表示局域表面等离激元共振的医学、材料和传感器论文。
- IBM 文档中的大型系统性能参考缩写。
- Zenodo 数据记录和聚合页是数据或元数据，不是独立研究论文。
- OpenAlex 把建筑火灾综述接到 LSPR23 被引链的一条边未获 ScienceDirect、题名、摘要或全文支持，按索引异常排除。
- 同一论文的 SSRN、聚合页、作者页、机构页和 Zenodo 伴随记录按一个研究工作合并，不重复计数。

## Dijk 2024 用户全文升级记录

- 原件：`raw/papers/datasets/1-s2.0-S2214212624001492-main.pdf`，保持原位，未复制、重命名或修改。
- 题名、DOI、作者、14 页和文章号均与 JISA 正式题录一致。
- SHA-256：`d28b3dd264ab41efa270c76c62c325454ec48e40b87bc0fd2a1bc512ee40dc4`。
- 全文确认：16,353,511 流、1,644,599 恶意流；Suricata 签名 F1 0.531；RF 4:1 切分，精确率 0.999、召回率 0.994、F1 0.997。
- 全文仍未知：是否明确使用全表、是否抽样、具体 RF 超参、实际输入字段、随机种子、分层／时间／主机／连接隔离、源码。
- 笔记：`wiki/papers/datasets/LSPR24/Dijk-2024-LSPR23数据集与随机森林复现.md`。
- Zotero：父条目 `CDDWA2UR`，本地原件链接子附件 `NAPDXPQS`。

## A 类全文核验字段

- 正式题名、作者、年份、载体、DOI／稳定 URL
- 使用年度版本与官方文件名／字段版本
- 完整官方原始表、子集、抽样或删行状态；无法确认时写“未知”
- 任务与预测单位
- 划分与防泄漏协议
- 模型与训练预算
- 指标、原始结果及页码／表号
- 可复现性缺口与不可直接声称内容
- 仓库原件、笔记、索引与 Zotero 状态

## 疑点关闭状态

1. **LSPR23 非字面下游研究**：数据 DOI、原论文正式 cited-by、OpenAlex、ScienceDirect、作者页和文件名搜索均已核验；只增加已知 A、5 篇 B 和索引噪声，没有新增 A。
2. **LSPR25 额外研究**：Zenodo、Crossref、OpenAlex、SSRN、arXiv、插件和作者页只确认 Dijk 等 2026；没有发现第二篇可核验学位论文或预印本。正式 *Computer Networks* DOI 仍待未来触发重审。
3. **别名增量**：`Locked Shields Packet Repository`、`Locked Shields flow dataset`、文件名和短横线／空格变体没有产生新增 A，只带出旧私有 Locked Shields 工作和缩写噪声。
4. **作者／引用链无缩写工作**：已检查 Dijk、Meier、Pihelgas、Vaarandi、Leoste 及正式参考／被引链；没有新增公开 LSPR23／24／25 直接使用工作。

这些疑点仅在截至 2026-08-11 的公开检索范围内关闭；出现新 DOI、被引增长、作者新作或 6 个月复查周期时重新打开。
