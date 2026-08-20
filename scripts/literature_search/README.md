# 关键词与向量混合文献检索

该工具只读取 `wiki/papers/**/*.md` 中具有合法 YAML 前言和非空 `source_pdf` 的论文笔记。所有 `INDEX.md`、缺少原件字段的参考笔记和 YAML 无法解析的文件都会排除，并在构建收据中按原因列出。工具不会读取 PDF，不会修改笔记、原件或 Zotero。

## 环境

依赖只由该目录的 uv 项目管理，不修改系统 Python，也不使用全局包：

```bash
uv sync --project scripts/literature_search --locked
```

模型使用 `intfloat/multilingual-e5-small` 固定修订，首次完整构建会下载约 488 MB 到项目缓存。默认在 Apple 芯片上使用 MPS，MPS 不可用或发生运行时错误时自动回退 CPU；也可用 `--device cpu` 强制 CPU。可用 `--model-cache` 指定缓存目录，或在缓存准备好后加 `--offline` 禁止网络。

## 命令

```bash
# 完整构建
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search build

# 不安装向量依赖时先构建中文词法索引
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search build --lexical-only

# 查询与状态
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search query \
  "正常性漂移异常检测" --mode hybrid --top-k 10
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search status --json

# 冻结对照集
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search evaluate --offline

# 论文笔记合同检查
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search lint wiki/papers/目标笔记.md --strict --json
```

`build --json` 与 `status --json` 会输出当前语料相对索引的 `added`、`changed`、`deleted`、`unchanged`，以及 `excluded`、`excluded_reasons`、`embedding_contract_changed` 和 `stale_reasons`。构建收据另含向量块级的 `reused` 与 `reembedded`。

## 论文身份与元数据

- YAML 由 PyYAML 的 `safe_load` 解析，标量与列表都会进入规范字段；无效 YAML 不再用逐行字符串解析器猜测。
- `paper_id` 优先使用规范 DOI，其次使用去版本号后的规范 arXiv 标识，最后使用规范题名和年份。
- `note_id` 是仓库相对路径。一篇论文可以对应多个笔记视图；查询默认按 `paper_id` 聚合，每条结果的 `note_views` 保留全部视图，`note_path` 指向最终证据块所在视图。
- 当前论文 DOI 和 arXiv 标识只读取 YAML 的 `doi`、`arxiv_id`。正文 DOI 仅保存为 `cited_dois`，不会参与当前论文身份生成。
- `title_zh`、`authors`、`year`、`aliases`、`tags`、`key_finding`、`tasks`、`datasets`、`methods`、`metrics`、`supports` 和 `cannot_support` 保存为结构化列，同时进入可检索的元数据分块。旧笔记的单数 `task/dataset/method/metric` 会兼容映射到对应复数字段。

## 增量构建

构建仍先写同目录临时 SQLite 文件，提交成功后再原子替换目标索引。若旧索引存在，构建器只读打开旧库，并且仅在稳定分块键和嵌入合同哈希同时相等时复制原始 `float32` 向量字节。稳定分块键包含规范笔记路径、标题、块位置、文本哈希和嵌入合同哈希；合同包含模型、修订、查询与文档前缀、解析和分块版本及字符预算。模式迁移、模型或分块合同变化会使旧向量整体失效。

## 结果解释

- 词法和向量通道先分别从分块聚合到笔记，再按 `paper_id` 聚合到论文；RRF 使用论文级排名，不会因同一论文存在多个笔记而重复占位。
- 每条结果同时输出 `lexical_block`、`vector_block` 和 `evidence_block`，以及两个通道的排名、原始分数和 RRF 贡献。
- 混合模式的最终证据块来自 RRF 贡献更大的通道；贡献相同时固定选择词法通道。`snippet/page_hint/note_path` 都与 `evidence_block` 一致，不再无条件优先词法片段。
- JSON 输出保留全部结构；文本输出显示论文身份、视图、最终证据通道、块号和标题。

## 冻结评估

`evaluate` 支持一条查询对应多个相关论文，并报告 Recall@5/10、MRR@10、nDCG@10、论文级去重、查询延迟、页码、原件存在性、负例返回数和词法/向量独有相关项。查询可选提供 `relevant_chunk_ids` 或 `relevant_chunk_keys` 作为块级真值；没有真实块标注时，块命中返回 `null`，不会用相关笔记路径冒充块级真值。

当前没有经独立开发集冻结的可靠拒答门。负例只报告返回数量，不使用冻结测试查询事后选择阈值。

查询集使用 `literature-query-set/v2` 时可声明 `dataset_id`、`dataset_role`、`qrel_status` 和 `tuning_prohibited`。本仓库严格区分：

- `curated-regression-v1`：从证据矩阵和题录人工构造的开发/回归集，不代表真实用户查询分布，可用于接口回归但不得冒充用户效果。
- `real-user-query-v1`：只含本会话与文献检索直接相关的用户原问，角色为独立验收，禁止据其结果调整 BM25、RRF 或阈值。当前规格位于 `.Codex/docs/2026-08-20-本地文献混合检索真实用户查询/real-user-query-v1.json`。

逐查询 `judgment_status` 不是 `complete` 或 `judged` 时，评估器只验证规格并标记 `skipped_pending_qrel`，不会运行检索或把它计作负例。相关路径与块必须在看排名前由全文或既有证据矩阵独立标注；标注完成后，两套集合分别输出指标，不能合并平均。

## 在线候选

`query` 使用统一范围：

- `--scope local`：只返回本地全文笔记证据，默认值。
- `--scope online`：只返回外部题录或摘要候选及来源状态。
- `--scope all`：分区返回本地证据与外部候选，二者不混排分数。

在线输出继续以 `results`/`paper_candidates` 保存论文候选，并独立提供 `code_candidates` 和 `hub_candidates`。代码与 Hub 候选不进入论文 RRF 或论文候选去重。

```bash
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search query \
  "normality shift anomaly detection" --scope all --mode lexical --json
```

可选环境变量只从进程环境读取，不写入索引或输出：

- `OPENALEX_API_KEY`：启用 OpenAlex `search.semantic`；缺失时直接标记 `skipped_missing_key`，不发出普通搜索请求。
- `SEMANTIC_SCHOLAR_API_KEY`：以 `x-api-key` 头发送；缺失时使用公共接口。
- `CROSSREF_MAILTO`：进入 Crossref 礼貌池。
- `GITHUB_TOKEN`：可选 GitHub REST 认证；缺失时只查询公开仓库并记录较低配额。
- `HF_TOKEN`：可选 Hugging Face 公开读取认证；缺失时使用匿名公开 API。

三个来源并发执行，但 Crossref 通过进程内锁保持单飞。HTTP 429 或 503 只有在响应提供数值型 `Retry-After` 且等待不超过本次超时时才退避并重试一次；403、超时、网络或 JSON 错误直接记录为来源级失败。在线候选按 DOI、arXiv、规范题名加年份依次跨来源去重，保留 `providers` 和各来源记录。

每个来源状态记录认证、延迟、缓存、限流、重试、退避、去重和降级原因。当前没有查询缓存，状态固定标记 `cache_kind=none`；后续若实现持久缓存，必须另行冻结过期和失效合同。`--offline` 会把全部在线来源标为 `skipped_offline`。`scope=all` 始终保留本地结果。所有在线结果均标记为未核全文候选，不自动写入 `raw/`、`wiki/` 或 Zotero。

GitHub 候选返回规范仓库 URL、`owner/name`、描述、主页、许可证、星数、归档状态、更新时间与默认分支，普通命中固定为 `unverified_code_candidate`。HF Papers 按 arXiv、DOI、题名与其他论文来源去重；HF 模型、数据集和 Space 独立返回仓库类型、任务、下载、点赞、更新时间、门控、许可证和 arXiv 关联。只有 Hub 元数据显式包含 arXiv 关联时标为 `paper_linked_candidate`，普通命中固定为 `unverified_hub_candidate`。本工具不自动下载、登录、上传、索引或认领任何外部候选。

## 可再生制品

- 默认索引：`.cache/literature-search/index.sqlite3`
- 默认模型缓存：`.cache/literature-search/model-cache/`
- uv 独立环境：`scripts/literature_search/.venv/`
- 清理索引：删除上述 SQLite 文件；下次 `build` 会原子重建。
- 清理模型：使用 `hf cache list` 确认条目，再用 `hf cache rm model/intfloat/multilingual-e5-small --dry-run` 预检。
- 索引和模型缓存都不应提交 Git。

`status` 会按当前索引合同重新扫描合法论文笔记并计算来源清单哈希；`stale=true` 时，`stale_reasons` 会指出来源新增、修改、删除或嵌入合同变化。

## 笔记 lint

- `paper-note-search/v1` 笔记自动进入严格模式；`--strict` 可对任意笔记强制执行同一合同。
- 严格模式检查 YAML 类型、DOI/arXiv 或题名年份身份、`raw/papers/` 原件、全文核验、页码锚点、支持/不能支持分区和关系字段，错误时退出码为 1。
- 旧模板默认使用兼容报告模式：缺失的新字段和分区只产生警告，YAML 无法解析等基础错误仍会失败。
- lint 只读文件并输出 `auto_modified=false`，不会自动修复或批量重写旧笔记。
- 可执行示例与入库清单位于 `.agents/skills/indexed-paper-reading/references/`。
