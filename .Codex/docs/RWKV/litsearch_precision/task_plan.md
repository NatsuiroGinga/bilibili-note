# Task Plan: 本地文献混合检索精度评测与改进

## Goal
在**真实查询测试集**上实测本地混合检索（lexical/vector/hybrid）基线四项指标，找出失败模式，做 1-2 项最小改进验证，按性价比排序给出建议。

## 硬约束
- 不碰 `.worktrees/`、不改 `wiki/` `raw/` Zotero、不连服务器、不跑训练
- 依赖走 `uv add`（在 `scripts/literature_search/` 内），禁 sed、禁 black
- 与 litsearch_vector_fix 代理避免同文件冲突：**我不改 `embeddings.py` / `pyproject.toml` / `uv.lock`**

## Phases
- [x] Phase 0: 摸清现状（读 README/evaluate.py/evaluation_queries.json/status）
- [ ] Phase 1: 读核心源码（search/ranking/lexical/documents/storage/embeddings）
- [ ] Phase 2: 从历史会话挖掘真实查询需求
- [ ] Phase 3: 构造 ≥20 条真实测试集 + 人工核对相关笔记（打开笔记核对）
- [ ] Phase 4: 扩展 evaluate.py 支持多相关文档 + Recall@5/10、MRR、nDCG@10
- [ ] Phase 5: 三模式基线评测（vector 取决于向量代理是否完成）
- [ ] Phase 6: 失败模式分析（举具体查询与错误命中）
- [ ] Phase 7: 调研改进手段（HF 模型 + 联网证据）
- [ ] Phase 8: 最小验证 1-2 项改进，实测对比
- [ ] Phase 9: 性价比排序 + 报告落盘 + 提交

## 现状事实（Phase 0 实测）
命令：`python3 -m scripts.literature_search status --json`
- note_count=525, chunk_count=6961, **vector_count=0, vector_dimension=0**
- stale=false, schema_version=1, built_at=2026-08-28T07:26:12Z, build_seconds=1.112
- source_manifest_hash=1e62a9acce43c2b13eb27ad49d78dabf46eb35cf94d053353247e23288cd9e0e
- 配置：chunk_max_chars=400, chunk_overlap_chars=80, rrf_constant=60, default_top_k=10, batch_size=16
- 模型：intfloat/multilingual-e5-small @ 614241f622f53c4eeff9890bdc4f31cfecc418b3

既有对照集 `evaluation_queries.json`：
- 仅 **5 条**查询，top_k=5，每条**恰好 1 条**相关路径
- 指标只有 `hit_rate_at_k`（= Recall@5，单相关文档时）与 `mean_reciprocal_rank`
- 无 Recall@10、无 nDCG，无多相关文档支持
- `frozen_before_first_run: true` —— 冻结集，不得改动

## Key Questions
1. 向量通道何时可用？（vector_count>0 才能评 vector/hybrid）
2. hybrid 融合当前实现是 RRF 还是加权？rrf_constant=60 提示 RRF
3. 分块 400 字符是否过小？6961/525 ≈ 13.3 块/篇
4. 真实查询分布是什么样？中文为主还是中英混合？

## Decisions Made
- 新测试集独立落盘 `evaluation_queries_real.json`，不动冻结集
- 评测脚本独立写 `evaluate_real.py`，不改冻结的 `evaluate.py`（避免与向量代理冲突）

## Errors Encountered
（待记录）

## Status
**全部完成（Phase 9）** —— 报告见 `.Codex/docs/RWKV/2026-08-28-文献检索精度评测与改进方案.md`

## 已完成
- Phase 1-3：读完核心源码；会话转录挖掘失败（零命中），改用仓库主题出题；
  建成 25 条测试集 `scripts/literature_search/evaluation_queries_real.json`（61 条相关路径，四类意图）
- Phase 4-5：写 `evaluate_real.py`（Recall@5/@10、MRR、nDCG@10，支持多相关文档）；
  lexical 基线 0.8575 / 0.9226 / 0.7933 / 0.7958；**vector 与 hybrid 未测量**（vector_count=0）
- Phase 6：主导失败模式为 INDEX.md 霸占首位（40% 的第 1 名 vs 2.9% 语料占比）；
  次要为 frontmatter 被整体丢弃、保形/共形同义异写
- Phase 7：调研嵌入模型（体积经 hf_fs 实测）、重排序、RRF、分块、查询改写
- Phase 8：V1/V2/V3 三变体实测，V3 达 0.9332 / 0.9556 / **1.0000** / 0.9657；
  另实测分块聚合改 Top-N 求和为**否定结果**
- Phase 9：报告落盘并提交

## Errors Encountered
- `mcp__ccd_session_mgmt__search_session_transcripts` 对检索式关键词零命中 →
  改用仓库 525 篇笔记的实际主题分布出题，并在报告中如实记为测试集局限
- `dump_notes.py` 初版把内联 YAML 数组 `tags: [a, b]` 当作标量逐字符迭代 →
  已修正为解析内联数组；该缺陷只影响我的统计脚本，不影响生产代码
- 向量修复代理的 `uv sync` 持续 21 分钟未完成 →
  未抢占其 venv，vector/hybrid 如实标为「未测量」，不以推演代替
