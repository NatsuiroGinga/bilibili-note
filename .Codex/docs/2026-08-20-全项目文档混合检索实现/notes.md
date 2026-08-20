# 全项目文档混合检索实施笔记

## 已核对证据

- 架构审计提交：`695d4d3`。
- GitHub 与 Hugging Face 候选通道提交：`1c70406`。
- Google Scholar 候选通道提交：`03982e4`。
- 现有索引只扫描 `wiki/papers/**/*.md`，按 `paper_id` 从分块聚合到论文，并保留原件与页码证据。
- 现有构建器通过稳定分块键和嵌入合同哈希复用原始 `float32` 向量，使用临时库原子替换。
- 审计盘点共 1701 个 Markdown、约 14.1 MB；最大活动 Markdown 约 124 KB，当前无需近似最近邻。

## 并行改动边界

开始时已有下列与本任务无关的工作树改动，本任务不会回滚或提交它们：

- `.gitignore`
- `scripts/literature_search/embeddings.py`
- `scripts/literature_search/lexical.py`
- `scripts/literature_search/requirements.txt` 删除
- 若干第三章、第四章实验工具、配置、启动器和报告。

## 拟定 collection

| collection | scope | 语料 |
|---|---|---|
| `papers` | `paper` | 具有合法 YAML 和 `source_pdf` 的全文论文笔记 |
| `route-control` | `project` | 路线总控、长期规则和当前合同 |
| `recovery` | `project` | 当前章节恢复卡；兼容页标记为已取代 |
| `plans` | `project` | 实施计划和 `task_plan.md` |
| `reports` | `project` | 实施、审查和结果报告 |
| `research-notes` | `project` | 活动研究笔记、结构化知识与说明文档 |
| `experiment-receipts` | `experiment` | 精确文件名允许清单下的聚合 JSON 收据 |
| `thesis-chapters` | `thesis` | `thesis/chapters/` 正文 |
| `output-deliverables` | `thesis` | `output/` 高层交付 Markdown |

## 待验证

- 真实小规模构建后的各 collection 文档数、分块数、索引字节和构建延迟。
- `paper/project/experiment/thesis/all` 的 collection 隔离和元数据回显。
- 对同一小规模语料重建时 `added/changed/deleted/unchanged` 收据与向量复用行为。

## 首次真实构建收据

- 索引：`/tmp/project-doc-search-20260820.sqlite3`。
- 模式：词法索引，真实全仓允许语料，非人工夹具。
- 文档：1701；分块：34464；构建时间：6.696 秒；索引：119787520 字节。
- collection：`papers=500`、`research-notes=753`、`plans=198`、`reports=182`、`route-control=10`、`recovery=3`、`experiment-receipts=19`、`thesis-chapters=19`、`output-deliverables=17`。
- 排除：83；其中归档、备份或敏感路径 43，忽略目录 13，`INDEX.md` 19，非法论文 YAML 1，缺原件论文候选 2，私有地址内容 5。
- 首次 `status` 收据：`stale=false`，1701 个文档全部 `unchanged`，各 collection 的 `added/changed/deleted` 均为 0。
- `all` 词法查询进程端到端延迟 0.23 秒；JSON 分开 `paper/project/experiment/thesis`，每条结果均回显 collection、权威、状态、证据等级和路径。
- 数据库直接核验 `INDEX.md` 入库数为 0；`RWKV当前恢复卡.md` 被标记为 `superseded`，默认查询状态门会排除它。

## 首次构建后修正

- 规则文件分类优先级高于目录分类，避免 `thesis/chapters/AGENTS.md` 和 `output/AGENTS.md` 被标成论文正文或交付物。
- 历史 PINN/R2 的两份 `output/` 恢复文档改归 `recovery`，标记 `route=PINN-R2`、`status=superseded`，不再进入默认 RWKV 或论文作用域。
- 增加 `parser_contract_hash` 并将解析合同版本升为 2，使分类、语料允许清单、收据允许清单和敏感过滤合同变化能够标记索引陈旧。
- 论文笔记只执行凭据和私钥拒绝，不会因全文包含数据集私有网段示例而误排；项目文档和实验收据仍额外拒绝私有地址。

## 最终增量构建收据

- 最终语料：1703 个文档、34496 个分块；构建 6.930 秒；词法索引 119803904 字节。构建期间其他代理新增两份活动计划文档，因此比首次收据多 2 份。
- collection：`papers=500`、`research-notes=749`、`plans=199`、`reports=182`、`route-control=19`、`recovery=5`、`experiment-receipts=19`、`thesis-chapters=18`、`output-deliverables=12`。
- 最终排除 83 份：归档、备份或敏感路径 43，忽略目录 13，`INDEX.md` 19，论文合同失败 3，项目私有地址内容 5。
- 最终 collection 迁移可在增量收据中见：两份历史路线文档从 `output-deliverables` 转入 `recovery`，规则文件转入 `route-control`，`thesis-chapters` 仅保留 18 份正文。

## 真实 E5 向量与混合查询收据

- 从仓库现有论文笔记、路线总控、第四章恢复卡、实施笔记、真实聚合 `summary.json`、论文正文和 `output` 交付物各选 1 份，以符号链接建立 `/tmp/project-doc-search-real-mini/`；没有创建人工语料。
- 默认模型 `intfloat/multilingual-e5-small@614241f...` 离线构建 7 个文档、120 个分块，生成 120 个 384 维 `float32` 归一化向量，CPU 耗时 9.081 秒，索引 819200 字节。
- `all --mode hybrid` 查询在 `paper/project/experiment/thesis` 四个分区均返回 `vector_block`：恢复卡向量分 0.898250，实验收据 0.879612，正文 0.867048，论文笔记 0.857757。进程端到端耗时 8.44 秒，包含模型加载。
- 第二次原子构建耗时 0.023 秒，`reused=120`、`reembedded=0`，7 个文档全部 `unchanged`，证明项目、实验和正文分块共用增量向量复用合同。
- 初次使用默认模型标识时，底层库在禁网环境仍尝试元数据解析。实现已在 `--offline` 且固定修订快照存在时自动改用本地快照路径；随后使用默认生产配置离线构建成功。
