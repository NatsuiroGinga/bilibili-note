---
name: literature-hybrid-search
description: 用户请求文献检索、相关工作、直接近邻、引用核验、研究空白、相似论文或主题论文时使用。
---

# 混合文献检索

## 目标

先复用仓库内已核全文的结构化笔记，再按证据缺口扩展外部候选。在线题录和摘要不能冒充全文证据。

## 工作流

1. 在仓库根运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`。
2. 索引存在且未陈旧时，运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search query "查询" --scope local --mode hybrid --offline --json`。按 `paper_id` 阅读去重结果，同时核对 `note_views`、`evidence_channel`、`evidence_block`、词法块和向量块。
3. 向量依赖不可用时可临时改用 `--mode lexical`，并在结果中明确缺失的通道。
4. 只有本地结果不足、用户要求近期外部工作或需要 DOI/题录核验时，移除 `--offline` 并将同一命令改为 `--scope all`。
5. 先报告最终证据块对应的本地笔记、其他视图、原件和页码；在线结果单列为“未核全文候选”，同时报告各来源认证、缓存、延迟、限流、去重和失败状态。OpenAlex 缺密钥时只报告 `skipped_missing_key`，不把跳过写成普通搜索回退。
6. 若用户决定正式纳入外部候选，停止本技能并转入仓库规定的原件下载、全文核验和知识库写回流程。

## 边界

- 不自动修改 `raw/`、`wiki/`、论文正文或 Zotero。
- 不因在线 API 失败丢弃本地结果。
- 不把 OpenAlex、Semantic Scholar 或 Crossref 的摘要、题录和搜索排序写成论文结论。
- 不根据负例查询的返回分数临时设置拒答阈值；可靠拒答门必须使用独立开发集冻结。
- 没有 `relevant_chunk_ids` 或 `relevant_chunk_keys` 时，不把相关笔记命中写成块级命中。
- `curated-regression-v1` 只作人工构造的开发/回归集，不得写成真实用户查询效果。
- `real-user-query-v1` 只作独立验收；相关性标注完成前不得查看或导出系统排名，也不得根据该集合调整 BM25、RRF 或阈值。
- 命令参数与重建方式以 `scripts/literature_search/README.md` 为准。
