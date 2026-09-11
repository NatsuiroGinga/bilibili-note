# 全项目文档关键词与向量混合检索

该工具在单一 SQLite 中按 collection 隔离论文笔记、活动项目文档、精选实验收据和论文正文。默认 `paper` 作用域仍只读取 `wiki/papers/**/*.md` 中具有合法 YAML 前言和非空 `source_pdf` 的论文笔记，并继续按 `paper_id` 去重。项目结果只显示自身证据等级，不能冒充论文全文。

所有 `INDEX.md`、归档、备份、缓存、依赖、运行大文件、检查点、逐样本预测、最终测试标签、原始大数组和疑似凭据内容都会排除，并在构建收据中按路径与原因列出。工具不会读取 PDF，不会修改文档、原件、实验制品或 Zotero。

## 环境

依赖只由该目录的 uv 项目管理，不修改系统 Python，也不使用全局包：

```bash
uv sync --project scripts/literature_search --locked
```

模型使用 `intfloat/multilingual-e5-small` 固定修订，首次完整构建会下载约 488 MB 到项目缓存。默认在 Apple 芯片上使用 MPS，MPS 不可用或发生运行时错误时自动回退 CPU；也可用 `--device cpu` 强制 CPU。可用 `--model-cache` 指定缓存目录；在缓存准备好后加 `--offline` 时，工具会将模型标识解析为该固定修订的本地快照路径，避免底层库再发起元数据请求。

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
  "正常性漂移异常检测" --scope paper --mode hybrid --top-k 10
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search query \
  "第四章当前实验状态" --scope project --mode hybrid --offline --top-k 10
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search status --json

# 冻结对照集
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search evaluate --offline

# 论文笔记合同检查
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search lint wiki/papers/目标笔记.md --strict --json
```

`build --json` 与 `status --json` 会输出当前语料相对索引的 `added`、`changed`、`deleted`、`unchanged`，以及逐 collection 的 `collection_diffs`、`excluded`、`excluded_reasons`、`embedding_contract_changed` 和 `stale_reasons`。构建收据另含 `collection_counts`、`collection_chunk_counts` 及向量块级的 `reused` 与 `reembedded`。

## 作用域与 collection

| 作用域 | collection | 用途 |
|---|---|---|
| `paper` | `papers` | 文献、相关工作、引用和机制来源 |
| `project` | `route-control`、`recovery`、`plans`、`reports`、`research-notes` | 当前路线、计划、状态和决策追溯 |
| `experiment` | `experiment-receipts` | 允许字段内的聚合运行状态与指标 |
| `thesis` | `thesis-chapters`、`output-deliverables` | 正文定位与公开表述 |
| `all` | 上述全部本地 collection | 明确跨域问题，按作用域分区输出 |

`local` 保留为 `paper` 的兼容别名；`online` 仍只返回外部候选。`--collection` 可在所选作用域内进一步过滤，参数可重复。默认只查询 `current/active/completed`；只有历史追溯请求才使用 `--include-history` 解锁 `superseded/rejected/archive`。

`--scope all` 仅用于明确跨域问题，并按 `paper/project/experiment/thesis` 证据泳道分组输出和使用。联邦 RRF 的全局排名只用于发现，不是证据权重或多数投票：运行事实优先原始 `experiment` 收据，当前裁决优先路线合同或恢复卡，外部机制依据只接受 `paper` 全文，`thesis` 只定位当前表述；同一事实的多份报告不得重复加权。

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

- `--scope paper`：只返回本地全文论文笔记证据，默认值；`local` 是兼容别名。
- `--scope project/experiment/thesis`：只返回相应本地 collection，不触发联网。
- `--scope online`：只返回外部题录或摘要候选及来源状态。
- `--scope all`：按 `paper/project/experiment/thesis` 分区返回本地证据，并保留外部候选独立分区；不同分区不比较原始分数。

在线输出继续以 `results`/`paper_candidates` 保存论文候选，并独立提供 `code_candidates` 和 `hub_candidates`。代码与 Hub 候选不进入论文 RRF 或论文候选去重。

```bash
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search query \
  "normality shift anomaly detection" --scope all --mode lexical --offline --json
```

可选环境变量只从进程环境读取，不写入索引或输出：

- `OPENALEX_API_KEY`：启用 OpenAlex `search.semantic`；缺失时直接标记 `skipped_missing_key`，不发出普通搜索请求。
- `SEMANTIC_SCHOLAR_API_KEY`：以 `x-api-key` 头发送；缺失时使用公共接口。
- `CROSSREF_MAILTO`：进入 Crossref 礼貌池。
- `GITHUB_TOKEN`：可选 GitHub REST 认证；缺失时只查询公开仓库并记录较低配额。
- `HF_TOKEN`：可选 Hugging Face 公开读取认证；缺失时使用匿名公开 API。
- `GOOGLE_SCHOLAR_MODE`：可选 `lookup` 或 `search`，默认传统关键词检索 `lookup`。`search` 仅在本机已有 Scholar 认证状态时执行，不会自动登录或静默回退。

在线来源并发执行，但 Crossref 通过进程内锁保持单飞。HTTP 429 或 503 只有在响应提供数值型 `Retry-After` 且等待不超过本次超时时才退避并重试一次；403、超时、网络或 JSON 错误直接记录为来源级失败。在线候选按 DOI、arXiv、规范题名加年份依次跨来源去重，保留 `providers` 和各来源记录。

每个来源状态记录认证、延迟、缓存、限流、重试、退避、去重和降级原因。当前没有查询缓存，状态固定标记 `cache_kind=none`；后续若实现持久缓存，必须另行冻结过期和失效合同。`--offline` 会把全部在线来源标为 `skipped_offline`。`scope=all` 始终保留本地结果。所有在线结果均标记为未核全文候选，不自动写入 `raw/`、`wiki/` 或 Zotero。

GitHub 候选返回规范仓库 URL、`owner/name`、描述、主页、许可证、星数、归档状态、更新时间与默认分支，普通命中固定为 `unverified_code_candidate`。HF Papers 按 arXiv、DOI、题名与其他论文来源去重；HF 模型、数据集和 Space 独立返回仓库类型、任务、下载、点赞、更新时间、门控、许可证和 arXiv 关联。只有 Hub 元数据显式包含 arXiv 关联时标为 `paper_linked_candidate`，普通命中固定为 `unverified_hub_candidate`。本工具不自动下载、登录、上传、索引或认领任何外部候选。

Google Scholar 通过本机 `scholar` 命令的参数列表调用，程序化查询固定使用 `--json`，禁止 shell 拼接。默认执行传统 `lookup`；缺命令、缺认证、限流、验证码、超时、非零退出或 JSON 错误只会使该来源降级。Scholar 候选固定标记 `unverified_external_candidate`；`clusterId`、引用数、期刊、排名和 PDF 发现链接只保存在 `provider_records` 中，不能升级为全文证据。工具不会运行 `scholar auth`、下载 PDF 或向 `raw/`、`wiki/`、Zotero 写入内容。

## 可再生制品

- 默认索引：`.cache/literature-search/index.sqlite3`
- 默认模型缓存：`.cache/literature-search/model-cache/`
- uv 独立环境：`scripts/literature_search/.venv/`
- 清理索引：删除上述 SQLite 文件；下次 `build` 会原子重建。
- 清理模型：使用 `hf cache list` 确认条目，再用 `hf cache rm model/intfloat/multilingual-e5-small --dry-run` 预检。
- 索引和模型缓存都不应提交 Git。

`status` 会按当前索引合同重新扫描全部允许语料并计算来源清单哈希；`stale=true` 时，`stale_reasons` 会指出来源新增、修改、删除或嵌入合同变化，`collection_diffs` 给出各 collection 的差异路径收据。

## 研究判断路由与检索收据

用户问题涉及数据集是否适合模型、机制选择、研究路线、跨文档实验判断、项目状态综合或文献依据时，先运行 `status --json`，再按问题选择唯一作用域运行 `query --mode hybrid --offline --json`。此规则只在形成研究结论时强制，不阻塞已满足数据和运行门禁的实验。

当 `status` 显示索引不存在或 `stale=true` 时，先执行构建并重新检查状态；调用方不得用陈旧结果作出研究结论。若模型依赖确实不可用，才允许 `--mode lexical` 降级，且答复中必须披露向量通道未运行。每次研究判断至少保存以下检索收据：`scope`、`mode`、索引 `manifest/hash` 或 `built_at`、`stale=false` 与关键命中路径。

本地 `query` 默认只在索引不存在或陈旧时自动构建；索引新鲜时绝不重建。`--no-auto-build` 可改为在不可用索引上直接拒绝并回显原因，`--auto-build-device {auto,cpu,mps}` 控制自动构建设备，`auto` 在 Apple 芯片上优先 MPS 后回退 CPU。`online` 不检查也不构建本地索引。手动与自动构建共用索引文件锁，后到进程会等待既有构建并重新检查状态，构建失败或构建后仍陈旧时一律拒绝查询。内容变化沿用稳定 `chunk_key` 仅重嵌入新增或变化分块；嵌入合同变化允许全量重嵌入，并在标准错误输出预计（无可比记录时明确为未知）与实际耗时。

`rg` 只用于混合结果后的精确代码、行号或已知字面量核验，不能替代语义发现。精确查找一旦扩大为研究判断，必须重新执行上述状态与混合查询。七篇文档等小样本构建只能标记为“架构验证”；只有覆盖全部允许语料并留有构建收据的结果才可标记为“全项目向量物化”。`real-user-query-v1` 是独立验收集，不参与 BM25、RRF、阈值或其他参数调节。

## 安全与证据边界

- 项目 Markdown 只从配置中的目录允许清单发现，并执行目录、文件名、大小和内容拒绝检查。
- `runs/` 不递归索引 Markdown 或原始制品；只有配置列出的聚合 JSON 文件名会进入实验收据适配器。
- 实验 JSON 只提取状态、运行身份、聚合指标、资源、时间和哈希等允许字段；路径、命令、地址、凭据、标签、逐样本数组和检查点字段不会写入索引。
- 每条结果强制回显 `scope`、`collection`、`doc_type`、`authority`、`status`、`evidence_level` 和原路径。只有 `papers` 结果提供 `paper_id`、原件和页码证据。

## 笔记 lint

- `paper-note-search/v1` 笔记自动进入严格模式；`--strict` 可对任意笔记强制执行同一合同。
- 严格模式检查 YAML 类型、DOI/arXiv 或题名年份身份、`raw/papers/` 原件、全文核验、页码锚点、支持/不能支持分区和关系字段，错误时退出码为 1。
- 旧模板默认使用兼容报告模式：缺失的新字段和分区只产生警告，YAML 无法解析等基础错误仍会失败。
- lint 只读文件并输出 `auto_modified=false`，不会自动修复或批量重写旧笔记。
- 可执行示例与入库清单位于 `.agents/skills/indexed-paper-reading/references/`。

## 已知故障与修复记录

### 2026-09-11 向量通道全链路不可用（`EmbeddingBackend` 缺少 `device` 形参）

**症状**：`build`（不带 `--lexical-only`）与 `query --mode vector|hybrid` 一律报错，只有 `build --lexical-only` 与 `query --mode lexical` 可用；`status --json` 长期显示 `vector_count: 0`、`vector_dimension: 0`、`vector_device: null`，索引停留在纯词法版本，因此容易被误读为「向量模型下载失败」。

**根因**：`device` 参数的接线不完整。`search.py`、`build.py`、`evaluate.py` 的四个 `EmbeddingBackend(...)` 调用点都已按关键字传入 `device=device`，但 `embeddings.py` 的 `EmbeddingBackend.__init__` 没有同步接收该形参，四处调用全部抛：

```text
TypeError: EmbeddingBackend.__init__() got an unexpected keyword argument 'device'
```

**与模型下载、网络和 HF 端点无关。** 本次实测：`https://huggingface.co` 直连返回 `http=200`（耗时 1.2 秒，不需要镜像端点）；固定修订 `614241f6...` 的完整快照已存在于 `.cache/literature-search/model-cache/`；`local_files_only=False`、`HF_HUB_OFFLINE=1`、本地快照路径三种加载方式分别耗时 5.8／1.4／1.8 秒，全部成功并在 `mps:0` 上完成编码。

**诊断命令**（先分清「索引无向量」与「模型不可用」）：

```bash
uv run --project scripts/literature_search --locked \
  python -m scripts.literature_search status --json
git show HEAD:scripts/literature_search/embeddings.py | rg -n "def __init__" -A 6
rg -n "EmbeddingBackend\(" scripts/literature_search/*.py
```

`status --json` 的 `vector_count: 0` 只说明索引是纯词法构建，**不等于**模型不可用。这类报错不要先改 `HF_ENDPOINT` 镜像或清空模型缓存——本例两者都不是原因，改动它们只会掩盖 TypeError 这一真实根因。

**修复**：`embeddings.py` 接收 `device` 形参（`auto`／`cpu`／`mps`）；`auto` 在 MPS 可用时优先 MPS，模型加载或编码抛 `RuntimeError` 时自动回退 CPU，并暴露 `device` 属性与 `fallback_reason` 供 `build`／`status` 记录。其余调用点无需改动。

**修复后验证收据**（2026-09-11 实测）：

| 项目 | 命令 | 实测结果 |
|---|---|---|
| 全量重建 | `build` | `vector_count: 156708`、`vector_dimension: 384`、`vector_device: "mps:0"`、`vector_device_fallback: null`、耗时 `1483.824` 秒、索引 `943484928` 字节 |
| 状态 | `status --json` | `exists: true`、`vector_count: 156708`、`vector_dimension: 384`、`vector_device: "mps:0"` |
| 混合查询 | `query "正常性漂移异常检测" --scope paper --mode hybrid` | 返回 `10` 条；前三条的词法／向量排名分别为 `1/1`、`2/2`、`3/15` |
| 增量复用 | 改动一份笔记后重新 `build` | `reused: 156760`、`reembedded: 1`，耗时 `33.0` 秒 |

前三条命中（`vector_score` 为归一化向量内积，查询侧 `query:` 前缀合同生效，前缀后带一个空格）：

| 排名 | `note_path` | 词法排名 | 向量排名 | `vector_score` |
|---|---|---|---|---|
| 1 | `wiki/papers/attack-detection/2023-Han-OWAD正常性漂移适应.md` | 1 | 1 | 0.915877 |
| 2 | `wiki/papers/attack-detection/2026-Kim-CANDI精选测试时适应.md` | 2 | 2 | 0.901550 |
| 3 | `wiki/papers/attack-detection/2026-Huang-RTTAD风险感知测试时适应.md` | 3 | 15 | 0.889848 |

本文件位于 `scripts/**/*.md`，属于索引语料：编辑后 `status` 会立即报 `stale=true`，需重新 `build`。该重建为增量，只重嵌入变化的分块，实测数十秒完成。

**构建期间没有进度输出属正常现象**：`_encode` 的 `show_progress_bar` 条件为 `len(values) > batch_size`，而 `_write_vectors` 每次只传入一个大小为 `batch_size` 的批次，条件恒为假。判断构建是否仍在推进，用文件大小而不是日志：

```bash
ls -la .cache/literature-search/index.sqlite3.tmp   # 每隔数十秒应持续增长
lsof -p <build_pid> | rg "com\.apple\.metal"       # 出现 Metal 库文件说明 MPS 后端已初始化
```

索引只有在全部向量写完后才原子替换正式文件；进程被杀会留下 `index.sqlite3.tmp`，下次 `build` 会自动删除并重来，无需手工清理。
