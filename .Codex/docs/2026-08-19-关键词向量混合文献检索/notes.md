# 研究与实现笔记：关键词与向量混合文献检索

## 本地盘点

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`
- 2026-08-19 实测 `wiki/papers/` 下有 507 个 Markdown 文件。
- 其中 491 个文件包含 YAML `source_pdf` 字段，118 个文件出现“页码”“page”或“p.”字样。
- 当前 Python 环境：`numpy==2.0.2`；向量模型运行依赖均未安装。
- 既有 `scripts/import_raw_papers_to_zotero.py` 会生成包含 `title`、`source_pdf`、`key_finding` 等 YAML 字段的笔记，但旧笔记格式不完全一致，解析器必须容忍带引号和 Obsidian 双向链接两种 `source_pdf` 形式。

## 初步架构

- 索引单元：Markdown 笔记的分块，而不是整篇 PDF。
- 元数据：笔记路径、标题、原件路径、章节标题、可提取页码线索、内容哈希、分块序号。
- 词法通道：对规范化后的字符生成 2 至 4 元 n-gram，以 BM25 计算分块分数，再聚合到笔记。
- 向量通道：使用官方模型卡确认的中英多语种文本嵌入；查询与文档分别遵循模型卡前缀合同。
- 持久化：SQLite 存元数据和统计，向量以定长 `float32` 二进制保存；查询时用 NumPy 精确点积。
- 融合：按两个通道各自排名做倒数排名融合，通道缺失时仅累加存在的排名贡献。

## 待核验证据

- 候选模型的模型卡、权重体积、许可证、维度、最大输入长度和编码前缀。
- `sentence-transformers` 或更小依赖栈在目标版本下的正式接口。
- 倒数排名融合原始论文或可信技术来源中的公式与常用常数来源。
- BM25 参数与字符 n-gram 范围的直接或任务化依据。

## 已核验外部合同

- Hugging Face `intfloat/multilingual-e5-small`：MIT，117,654,272 参数，384 维，支持中英文在内的 100 种语言；所有查询与段落须分别加 `query: `、`passage: ` 前缀；最多 512 token。固定修订 `614241f622f53c4eeff9890bdc4f31cfecc418b3`，实际所需权重和分词配置约 488 MB。
- Sentence Transformers：Context7 `/huggingface/sentence-transformers` 核验到构造器支持 `revision`、`cache_folder`、`local_files_only`；编码接口支持 `batch_size` 与 `normalize_embeddings`。实现使用模型卡直接示例中的 `encode`，自行加入 E5 前缀。
- RRF 原始论文第 1 页公式为各通道 `1 / (k + rank)` 求和，`k=60` 经先导后冻结且后续验证未改。本仓库直接使用该值，不以本地对照集调参。
- OpenAlex 当前 `/works` 支持 `search` 与 `search.semantic`；语义检索按官方文档要求 API 密钥，单页 `per_page` 范围 1–100。
- Semantic Scholar Academic Graph `/graph/v1/paper/search` 接受纯文本 `query`、`limit` 和逗号分隔 `fields`；可匿名使用，若设置密钥则必须以 `x-api-key` 请求头传递。
- Crossref `/works?query.bibliographic=` 可作 DOI/题录核验；公共池无需认证，提供 `mailto` 时使用礼貌池。2025-12 起官方文档列出的公共/礼貌池速率分别为每秒 5/10，请求并发上限分别为 1/3。本实现每次查询只发一条 Crossref 请求。
- Codex 官方文档确认仓库根 `.agents/skills/<name>/SKILL.md` 会被扫描，技能可由描述隐式匹配；技能变化通常自动发现，未出现时重启 Codex。

## 规则冲突裁决

- `raw/AGENTS.md` 要求提及外部论文时下载原件并写笔记，但父任务明确禁止本实现触碰 `raw/`、`wiki/` 和 Zotero。故 RRF 与模型资料只作为当前实现依据记录在过程文档，未执行入库；交付时必须显式保留此未关闭证据治理项。

## 边界

- 本任务不新增或修改任何论文笔记、原始 PDF、资源笔记或 Zotero 条目。
- 对照集只用于工具的检索行为检查，不属于论文实验，也不据此形成方法有效性结论。
