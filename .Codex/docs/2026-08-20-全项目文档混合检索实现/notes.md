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
