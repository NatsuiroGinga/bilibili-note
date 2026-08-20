# 本地文献混合检索优化审计笔记

## 审计快照

- 日期：2026-08-20
- 代理：`gpt-5.6-sol`
- 推理强度：`high`
- 工作树中检索工具源码与技能已有未提交改动，本任务不拥有这些文件，只读审计当前内容。

## 本地证据

- 当前状态：索引存在但 `stale=true`；构建于 `2026-08-20T09:12:33Z`，511 篇、6854 块、6854 个 384 维向量、37,617,664 字节，CPU 全量构建 348.798 秒。
- 陈旧差异只有 1 篇新增论文笔记和 1 个修改后的 `INDEX.md`，现实现仍要求全量重嵌入。
- 输入通配符实际包含 14 个 `INDEX.md`，它们不是论文全文笔记。
- 当前 YAML 解析器只把 `title`、`source_pdf`、`doi` 送入 `NoteDocument`；`authors`、`year`、`aliases`、`tags`、`key_finding`、`method` 等被前言剥离后不进入检索。
- 当前 512 个 Markdown 文件中：`title/tags/date` 各 512，`authors/year/source_pdf` 各 496 左右，`aliases` 335，`method` 231，`doi` 65；现有索引无法利用大部分结构化字段。
- 索引中有 34 组重复标题、22 组重复 DOI。部分 DOI 是解析器从正文前 4000 字符抓到的“被引用论文 DOI”，不能作为当前笔记的规范身份。
- 分块平均 262.7 字符，最大 451 字符；204 块短于 64 字符。固定 E5 分词器实测中位数 146 token、95 分位 237、最大 303，没有超过 512 token，当前不存在截断损失证据。
- 向量矩阵为 `(6854, 384)`，占 10,527,744 字节。5 次只读诊断中，热加载中位数 39.113 ms，精确矩阵点积中位数 0.742 ms；当前瓶颈不是精确余弦。
- 当前主机 `arm64`，PyTorch 已构建 MPS 支持但 `torch.backends.mps.is_available()` 为假；本次构建事实为 CPU。
- 混合结果的展示片段总是优先取词法最佳块，即使向量块更能解释命中，证据片段可能与融合排序原因不一致。
- 在线来源按 OpenAlex、Semantic Scholar、Crossref 串行调用，单来源超时 8 秒时总延迟可累加；没有跨来源去重、查询缓存和退避。

## 外部一手资料

### SQLite

- 查询式：`SQLite FTS5 official documentation trigram tokenizer contentless delete BM25`
- URL：<https://www.sqlite.org/fts5.html>
- 访问日期：2026-08-20；目标机 SQLite：3.51.0。
- 采用：trigram 是连续三字符子串；短于三字符的全文查询无命中；内置 BM25 固定 `k1=1.2`、`b=0.75`；普通 contentless 表不直接支持 UPDATE/DELETE，3.43.0 起的 `contentless_delete=1` 支持完整列更新。
- 排除：不因存在更新接口就直接改为在线原地写；当前原子替换和不可变只读连接有更简单的一致性边界。

- 查询式：`SQLite WAL concurrency official`
- URL：<https://www.sqlite.org/wal.html>
- 访问日期：2026-08-20。
- 采用：WAL 允许读写并发，但只有一个写者，要求同一主机，并引入检查点与 `-wal/-shm` 文件管理。
- 排除：当前单机构建后原子替换无需 WAL；只有改成共享可写增量库并出现真实并发阻塞时才启用。

### E5、Sentence Transformers 与 NumPy

- 查询式：`intfloat multilingual-e5-small model card query passage prefix 512`
- URL：<https://huggingface.co/intfloat/multilingual-e5-small>；固定修订 `614241f622f53c4eeff9890bdc4f31cfecc418b3` 的本地官方模型卡与配置。
- 采用：384 维；查询与文档分别要求 `query: `、`passage: `；最大 512 token；缺前缀会降质。
- 当前核验：实现前缀正确；6854 块最大 303 token，无截断。

- 查询式：`Multilingual E5 Text Embeddings technical report original`
- URL：<https://arxiv.org/abs/2402.05672>
- 采用：多语种 E5 基于约 10 亿多语文本对预训练并在多语检索任务上评估。

- 查询式：`Sentence Transformers normalize embeddings retrieve rerank batch size official`
- URL：<https://sbert.net/docs/package_reference/sentence_transformer/model.html>、<https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html>
- 版本：工作树锁定 `sentence-transformers==5.1.1`。
- 采用：归一化后可用点积；批量大小应按硬件与输入长度实测；交叉编码器适合作为候选集的第二阶段重排器。

- 查询式：`NumPy 2.0 matmul official`
- URL：<https://numpy.org/doc/2.0/reference/generated/numpy.matmul.html>
- 版本：工作树锁定 `numpy==2.0.2`。
- 采用：二维矩阵与一维向量执行矩阵乘法并可由 BLAS 加速；与单位归一化向量结合时，当前 `vectors @ query_vector` 是精确余弦排序。

### 融合、重排和规模边界

- 查询式：`Reciprocal Rank Fusion Cormack Clarke Buettcher original PDF`
- URL：<https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf>
- 采用：原始公式为各排名 `1/(k+rank)` 求和；`k=60` 是原论文先导后冻结的设置，不是本仓库普适最优值。

- 查询式：`Analysis Fusion Functions Hybrid Retrieval original`
- URL：<https://arxiv.org/abs/2210.11934>
- 采用：后续研究指出 RRF 对参数敏感，带少量标注的归一化分数组合可能优于 RRF。因此保持 RRF 作为无监督基线，但须在扩充评估集后比较，不应凭原论文常数冻结本任务结论。

- 查询式：`BGE M3 multilingual dense sparse multi-vector original`
- URL：<https://arxiv.org/abs/2402.03216>
- 采用：近期模型可统一稠密、稀疏和多向量检索，并展示长文档能力。
- 排除：当前只有 6854 块，现有 E5 无截断且没有领域评估显示模型不足；现在切换 BGE-M3 会增加模型、索引和运行成本，属于无证据换架构。

- 查询式：`Faiss choose index exact flat few searches official`
- URL：<https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index>
- 访问日期：2026-08-20。
- 采用：官方指南强调少量查询时直接计算更合适，只有 Flat 保证精确结果；近似索引存在速度、召回、内存和训练成本权衡。
- 当前核验：本地精确点积热中位数 0.742 ms，不引入 Faiss、ANN 或向量服务。

- 查询式：`BEIR heterogeneous benchmark zero-shot original`
- URL：<https://arxiv.org/abs/2104.08663>
- 采用：多类型检索需要异质查询评估；BM25 是稳健基线，重排通常更强但计算成本更高。

- 查询式：`Query2doc query expansion original`、`HyDE zero-shot dense retrieval original`
- URL：<https://aclanthology.org/2023.emnlp-main.585/>、<https://arxiv.org/abs/2212.10496>
- 采用：查询扩展可能提高召回。
- 排除：生成式扩展可能引入虚构细节和非确定性；本仓库应先使用已核验别名、缩写和双语题名做确定性扩展，生成式扩展只作为后续受控实验。

### 在线来源与 Codex

- 查询式：`OpenAlex API semantic search API key changelog official`
- URL：<https://github.com/ourresearch/openalex-help/blob/main/content/api/semantic-search.md>、<https://help.openalex.org/hc/en-us/articles/38868153578263-Changelog>
- 采用：语义检索最长使用 2000 字符、最多 50 个结果、每秒 1 次；官方变更日志说明 2026-02-13 起所有 API 请求均要求密钥。
- 结论：当前“无密钥回退普通搜索”的说明已过时，应无密钥直接跳过并明确状态。

- 查询式：`Semantic Scholar Academic Graph API tutorial paper search official`
- URL：<https://www.semanticscholar.org/product/api/tutorial>
- 采用：API 密钥可选但推荐；无密钥共享配额；官方建议多数场景使用 bulk search，字段应最小化。当前每次只取 5 条且需要摘要，继续 relevance search 可接受，但必须缓存、退避和记录来源延迟。

- 查询式：`Crossref REST API access authentication rate limits official`
- URL：<https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/>
- 最近更新：2025-10-16。
- 采用：公共池 5 次/秒且并发 1，礼貌池 10 次/秒且并发 3；官方要求处理 403/429、监控延迟、退避并缓存重复请求。

- 查询式：`Codex save repeated workflows as skills official`
- URL：<https://developers.openai.com/codex/use-cases>
- 访问日期：2026-08-20。
- 采用：官方将反复执行的工作流保存为技能。是否采用仓库级技能仍由本仓库规则、触发边界和避免功能重叠共同裁决。

## 综合判断

- 当前主要风险是“索引了错误对象或错误身份、结构化证据没有进入检索、评估合同与真实输入不一致”，不是向量搜索规模。
- 保留 SQLite、FTS5、E5、NumPy 精确点积和 RRF 作为可审计基线；在扩充评估前不换模型、不上向量数据库、不加生成式查询扩展或交叉编码器。
- 建议新建仓库级薄编排技能，而不是修改通用 Zotero/Obsidian 技能来承载本仓库特有的 `raw/`、`wiki/`、`INDEX.md`、Git 快照和检索自检合同。该技能必须调用现有阅读与入库能力，不复制通用论文阅读方法。

## 未关闭问题

- 34 组重复标题和 22 组重复 DOI 中，哪些是应合并的重复笔记，哪些是同一论文面向不同研究路线的合法视图，需要知识库治理者裁决。
- 本任务未运行冻结效果查询，检索质量改进仍是待验证建议。
- 本机 MPS 当前不可用；若运行环境变化，批量大小和设备必须重新实测，不能照搬 `16`。
