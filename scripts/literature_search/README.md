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
```

`build --json` 与 `status --json` 会输出当前语料相对索引的 `added`、`changed`、`deleted`、`unchanged`，以及 `excluded`、`excluded_reasons`、`embedding_contract_changed` 和 `stale_reasons`。构建收据另含向量块级的 `reused` 与 `reembedded`。

## 论文身份与元数据

- YAML 由 PyYAML 的 `safe_load` 解析，标量与列表都会进入规范字段；无效 YAML 不再用逐行字符串解析器猜测。
- `paper_id` 优先使用规范 DOI，其次使用去版本号后的规范 arXiv 标识，最后使用规范题名和年份。
- `note_id` 是仓库相对路径。一篇论文可以对应多个笔记视图；索引保存 `paper_id -> note_id` 关系，为查询层按论文聚合并列出视图提供稳定接口。
- 当前论文 DOI 和 arXiv 标识只读取 YAML 的 `doi`、`arxiv_id`。正文 DOI 仅保存为 `cited_dois`，不会参与当前论文身份生成。
- `title_zh`、`authors`、`year`、`aliases`、`tags`、`key_finding`、`tasks`、`datasets`、`methods`、`metrics`、`supports` 和 `cannot_support` 保存为结构化列，同时进入可检索的元数据分块。旧笔记的单数 `task/dataset/method/metric` 会兼容映射到对应复数字段。

## 增量构建

构建仍先写同目录临时 SQLite 文件，提交成功后再原子替换目标索引。若旧索引存在，构建器只读打开旧库，并且仅在稳定分块键和嵌入合同哈希同时相等时复制原始 `float32` 向量字节。稳定分块键包含规范笔记路径、标题、块位置、文本哈希和嵌入合同哈希；合同包含模型、修订、查询与文档前缀、解析和分块版本及字符预算。模式迁移、模型或分块合同变化会使旧向量整体失效。

## 在线候选

`query` 使用统一范围：

- `--scope local`：只返回本地全文笔记证据，默认值。
- `--scope online`：只返回外部题录或摘要候选及来源状态。
- `--scope all`：分区返回本地证据与外部候选，二者不混排分数。

```bash
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search query \
  "normality shift anomaly detection" --scope all --mode lexical --json
```

可选环境变量只从进程环境读取，不写入索引或输出：

- `OPENALEX_API_KEY`：启用 OpenAlex `search.semantic`；缺失时尝试普通 `search` 并标记降级。
- `SEMANTIC_SCHOLAR_API_KEY`：以 `x-api-key` 头发送；缺失时使用公共接口。
- `CROSSREF_MAILTO`：进入 Crossref 礼貌池。

每次查询对每个来源至多发出一次请求。HTTP 403、429、超时、网络或 JSON 错误都会记录为来源级失败；`scope=all` 仍返回本地结果。所有在线结果均标记为未核全文候选，不自动写入 `raw/`、`wiki/` 或 Zotero。

## 可再生制品

- 默认索引：`.cache/literature-search/index.sqlite3`
- 默认模型缓存：`.cache/literature-search/model-cache/`
- uv 独立环境：`scripts/literature_search/.venv/`
- 清理索引：删除上述 SQLite 文件；下次 `build` 会原子重建。
- 清理模型：使用 `hf cache list` 确认条目，再用 `hf cache rm model/intfloat/multilingual-e5-small --dry-run` 预检。
- 索引和模型缓存都不应提交 Git。

`status` 会按当前索引合同重新扫描合法论文笔记并计算来源清单哈希；`stale=true` 时，`stale_reasons` 会指出来源新增、修改、删除或嵌入合同变化。
