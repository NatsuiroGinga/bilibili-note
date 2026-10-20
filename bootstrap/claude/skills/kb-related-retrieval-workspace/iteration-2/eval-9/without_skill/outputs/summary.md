# 检索结果汇总：Obsidian 知识库配置与知识图谱

检索源：research-knowledge MCP（lexical 模式 + obsidian-cli 兜底）作用于 `~/Dev/Research` Obsidian vault。

## 结论

- **Obsidian 知识库配置文档：有**，核心文档为 `Knowledge/obsidian-project-kb-setup.md`。
- **知识图谱相关文档：无专门文档**。仅在上述配置文档中有一句关于"图谱产物默认项"的说明；另有一处 GraphQL 命中与知识图谱无关。

## 命中文档详情

### 1. Obsidian 知识库配置（核心命中）

- 路径：`/Users/bilibili/Dev/Research/Knowledge/obsidian-project-kb-setup.md`
- Obsidian 跳转：`obsidian://open?vault=Research&file=Knowledge/obsidian-project-kb-setup.md`
- 内容要点：
  - 结论：Claude Scholar 内置 Obsidian 项目知识库工作流，filesystem-first（无需 MCP、无需 API key）。vault 结构即 `~/Dev/Research` 现有结构；通过 `.claude/project-memory/registry.yaml` 绑定 repo↔vault；主命令为 `/kb-*` 系列。
  - Vault 结构：`Research/{project-slug}/` 下含 `00-Hub.md / 01-Plan.md / 02-Index.md`、`Sources/`、`Knowledge/`、`Experiments/`、`Results/Reports/`、`Writing/`、`Daily/`、`Maps/`、`Archive/`、`_system/`（registry.md + schema.md + lint-report.md）。
  - 关键机制：绑定、笔记语言（registry.yaml 配置 > OBSIDIAN_NOTE_LANGUAGE 环境变量 > 默认 en）、内置 skills（obsidian-project-kb-core 等 5 个）、`/kb-*` 命令族。
  - 图谱相关内容（唯一）：默认自动维护的图谱产物仅 `Maps/literature.canvas`；其他 `.base` 视图或 canvas 均为 explicit-only。
  - CLI 与 URI：obsidian CLI 需开启 Desktop 的 Command line interface 设置；`obsidian://` URI 跳转格式；实测 `vault=Research` 匹配可能失效。
  - 生命周期：Detach / Archive / Purge 三态。
  - 关联文档：`Knowledge/knowledge-ingestion-workflow`、`Knowledge/mcp-handshake-timeout`。

### 2. 同源的 ingestion 暂存副本（非独立文档）

- `_ingestion-staging/20260827T174817+0800-obsidian-setup/decision-report.md`
- `_ingestion-staging/20260827T174817+0800-obsidian-setup/drafts/obsidian-project-kb-setup.md`

以上为 `obsidian-project-kb-setup.md` 落库前的暂存草稿/决策报告，与核心文档同源，无额外信息。

## 无关命中（排除）

- `manba-bi/Knowledge/data-passthrough-layered-debug.md`：命中为 GraphQL，与"知识图谱"无关。
- `README.md`、`_scan/notes.md`：命中为 wikilink 连接约定，非图谱配置。

## 检索过程备注

- MCP `knowledge_search`（lexical）自动作用域默认落在 `bban-api`，对 Obsidian 配置主题为空；通过 CLI 兜底全文检索与放宽关键词（`Obsidian vault`）才命中 common 作用域文档。索引当前共 40 个文件，状态正常（stale_files=0）。
