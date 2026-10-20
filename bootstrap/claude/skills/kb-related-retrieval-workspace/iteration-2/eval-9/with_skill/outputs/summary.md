# 检索结果：Obsidian 知识库配置 与 知识图谱

> 检索方式：research-knowledge MCP（`knowledge_search` scope=all，lexical + semantic）+ Obsidian CLI 兜底 + rg 文件系统兜底。
> 检索时间：2026-08-27。

## 检索结果

**结论：有。知识库中有 Obsidian 项目知识库配置的正式条目；"知识图谱"没有独立文档，但有图谱产物说明与一个实际 canvas 图谱。**

### 主命中（Obsidian 知识库配置）

- **obsidian-project-kb-setup**（`~/Dev/Research/Knowledge/obsidian-project-kb-setup.md`，common scope，status: active，2026-08-27 更新）
  - 摘要：Claude Scholar 内置 Obsidian 项目知识库工作流，**filesystem-first**（无需 MCP / API key）。vault 结构即 `~/Dev/Research` 现有结构；通过 `.claude/project-memory/registry.yaml` 绑定 repo↔vault；主命令为 `/kb-*` 系列（`/kb-init`、`/kb-status`、`/kb-ingest`、`/kb-log`、`/kb-sync`、`/kb-links`、`/kb-promote`、`/kb-index`、`/kb-lint`、`/kb-archive`、`/kb-map`、`/kb-literature-review`）。含 vault 结构（`Research/{project-slug}/` 下 00-Hub/01-Plan/02-Index、Sources/*、Knowledge/ Experiments/ Results/Reports/ Writing/ Daily/ Maps/ Archive/、_system/registry.md + schema.md + lint-report.md）、内置 skills（obsidian-project-kb-core、obsidian-source-ingestion、obsidian-literature-workflow、obsidian-kb-artifacts、defuddle）、CLI/URI、生命周期（Detach/Archive/Purge）。
  - 跳转：`obsidian://open?vault=Research&file=Knowledge/obsidian-project-kb-setup.md`

### 知识图谱相关

- **无独立"知识图谱"文档**。图谱相关内容散落在 obsidian-project-kb-setup 的"关键机制"中：默认自动维护的图谱产物仅 `Maps/literature.canvas`；其他 `.base` 视图或 canvas 均 explicit-only。
- 实际存在的图谱产物：**bban-api-knowledge.canvas**（`~/Dev/Research/bban-api/Maps/bban-api-knowledge.canvas`），bban-api 项目知识图谱 canvas，Obsidian 打开后可在 Graph View / Canvas 查看。manba-bi 与 te 的 Maps/ 目录为空。
- 全库未发现 Graph View / 图谱关键词的其他独立条目。

### 附属（同主题 staging 沉淀，尚未正式提升入检索索引）

- **decision-report.md**（`~/Dev/Research/_ingestion-staging/20260827T174817+0800-obsidian-setup/decision-report.md`）
  - 摘要：obsidian-project-kb-setup 的沉淀决策报告，来源为 `~/Dev/ba/docs/OBSIDIAN_SETUP.zh-CN.md`；原标记 status: draft、promotion: pending、retrieval: false（未加入允许清单/registry/索引）。
  - 跳转：`obsidian://open?vault=Research&file=_ingestion-staging/20260827T174817+0800-obsidian-setup/decision-report.md`
- **drafts/obsidian-project-kb-setup.md**（同 staging 目录下草稿）

> ⚠️ 索引注意：`knowledge_search`（lexical + semantic）与 `knowledge_cli_search` 均未直接命中主条目 obsidian-project-kb-setup.md，仅 rg 文件系统兜底命中。与 decision-report 标注的 `retrieval: false` 一致——该文档虽已位于 `Knowledge/`（status: active），但尚未纳入检索索引/允许清单。如需在 MCP 检索中直接命中，需将条目登记进 registry + 允许清单后 reindex。

## 关联文档

- 出链（主条目引用谁）：
  - `Knowledge/knowledge-ingestion-workflow.md`（沉淀工作流）
  - `Knowledge/mcp-handshake-timeout.md`（MCP 检索与握手）
- 入链（谁引用主条目）：`_ingestion-staging/20260827T174817+0800-obsidian-setup/decision-report.md`、`_ingestion-staging/.../drafts/obsidian-project-kb-setup.md`（均为本次沉淀来源，非正式知识条目）
- 同层相关 Knowledge/ 条目（common scope 检索/工作流家族）：`knowledge-ingestion-validation-status.md`、`local-knowledge-retrieval-evaluation.md`、`unmapped-project-documents.md`、`api-auth-environment-contract.md`
- 图谱产物：`bban-api/Maps/bban-api-knowledge.canvas`

## 图谱提示

可在 Obsidian 打开 `~/Dev/Research` vault 后：
1. 左侧图谱图标查看全局 Graph View 可视化图谱（wikilink 关联全库文档）。
2. 打开 `bban-api/Maps/bban-api-knowledge.canvas` 查看 bban-api 项目的显式知识图谱。
3. 主条目 obsidian-project-kb-setup 目前只有 2 条出链（knowledge-ingestion-workflow、mcp-handshake-timeout），入链均为 staging 临时文档，尚未形成稳定的图谱节点。
