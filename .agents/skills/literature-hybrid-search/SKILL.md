---
name: literature-hybrid-search
description: 用户请求文献检索、相关工作、直接近邻、引用核验、研究空白、相似论文或主题论文时使用。
---

# 混合文献检索

## 目标

先复用仓库内已核全文的结构化笔记，再按证据缺口扩展外部候选。在线题录和摘要不能冒充全文证据。

## 工作流

1. 在仓库根运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`。
2. 索引存在且未陈旧时，运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search query "查询" --scope local --mode hybrid --offline --json`。
3. 向量依赖不可用时可临时改用 `--mode lexical`，并在结果中明确缺失的通道。
4. 只有本地结果不足、用户要求近期外部工作或需要 DOI/题录核验时，移除 `--offline` 并将同一命令改为 `--scope all`。
5. 先报告本地笔记、原件和页码；在线结果单列为“未核全文候选”，同时报告各来源成功、限流或失败状态。
6. 若用户决定正式纳入外部候选，停止本技能并转入仓库规定的原件下载、全文核验和知识库写回流程。

## 边界

- 不自动修改 `raw/`、`wiki/`、论文正文或 Zotero。
- 不因在线 API 失败丢弃本地结果。
- 不把 OpenAlex、Semantic Scholar 或 Crossref 的摘要、题录和搜索排序写成论文结论。
- 命令参数与重建方式以 `scripts/literature_search/README.md` 为准。
