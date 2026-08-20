---
name: indexed-paper-reading
description: 用户要求把论文正式纳入本仓库 raw/papers 与 wiki/papers、补全已有全文论文笔记并确保本地混合检索可检出时使用。不用于仅搜索候选、普通摘要、相关工作综述或论文正文写作。
---

# 可索引论文阅读编排

## 目标

只编排本仓库特有的 `raw -> wiki -> INDEX -> Zotero -> 索引更新 -> 检索自检`。全文读取、题录管理和 Obsidian 写回分别复用现有 PDF、Zotero 与 Obsidian 技能，不复制通用阅读方法。

## 输入与输出

- 输入：本地 PDF、论文 URL、DOI、arXiv ID 或 Zotero 条目之一；目标主题目录；预期检索意图；是否允许更新已有笔记。
- 输出：规范原件、唯一 wiki 笔记、方向 `INDEX.md` 更新、Zotero 状态、lint 收据、增量索引收据和检索自检收据。

## 工作流

1. 读取根 `AGENTS.md`、`raw/AGENTS.md`、`wiki/AGENTS.md` 和仓库 `SCHEMA.md`，先查 DOI、arXiv、题名和现有双向链接，禁止重复入库。
2. 原件获取与全文读取调用 `document-skills:pdf` 或 `pdf-converter`；本技能不复述 OCR、页码核验和 PDF 提取方法。
3. Zotero 查询、导入、附件和引用键调用 `zotero:Zotero`；没有实际结果时只记录阻塞，不伪造条目键。
4. Obsidian 路由与链接修复调用 `obsidian-project-kb-core`、`obsidian-source-ingestion` 或 `zotero-obsidian-bridge`；仓库落点仍服从本地 `raw/`、`wiki/` 和 `INDEX.md` 规则。
5. 按 [paper-note-search-v1.md](references/paper-note-search-v1.md) 写唯一规范笔记，按 [checklist.md](references/checklist.md) 自检。
6. 运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search lint <笔记> --strict --json`。失败时只修目标笔记，不批量改写旧笔记。
7. 更新唯一对应方向的 `INDEX.md`，再运行 `status` 与增量 `build`，记录 `added/changed/reused/reembedded/excluded`。
8. 使用写笔记前冻结的 3 至 5 个检索意图执行本地混合查询，核对论文级结果、笔记视图和最终证据块。该自检不进入系统效果评估集。

## 失败边界

- 无全文、原件路径不存在或全文未核验：停止创建确定性论文笔记，只在 `.Codex/docs/` 记录候选和阻塞。
- DOI、arXiv 或题名身份冲突：停止索引更新，先由知识库治理者裁决是否为合法多视图。
- lint 失败：不得以删除字段、伪造页码、伪造 Zotero 键或修改旧笔记制造通过。
- 在线题录与摘要只能是候选，不得升级为全文证据或论文结论。
- 不自动修改论文正文、实验或无关知识库对象。
