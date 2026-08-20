---
name: literature-hybrid-search
description: 用户请求项目内文档、实验收据、论文正文、Google Scholar、学术搜索、文献检索、相关工作、直接近邻、引用核验、研究空白、相似论文或主题论文，或需要就数据集适配、机制选择、研究路线、跨文档实验判断、项目状态综合作出判断时使用。
---

# 混合文献检索

## 目标

先按 `paper/project/experiment/thesis` 识别本地证据作用域，再查询对应 collection。只有论文证据缺口需要外部发现时才扩展在线候选；项目文档、实验收据、论文正文、在线题录和摘要都不能冒充已核论文全文。

## 工作流

1. 对数据集适配、机制选择、研究路线、跨文档实验判断、项目状态综合或文献依据等研究判断，在仓库根先运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`。这一步只在形成研究结论时强制，不阻塞已经满足数据和运行门禁的实验。
2. 索引不存在或 `stale=true` 时，先依照 README 进行增量或完整构建，再重新运行 `status`；不得用陈旧结果支撑研究结论。只有模型依赖确实不可用时可临时改用 `--mode lexical`，并在答复中明确向量通道未运行。
3. 索引存在且 `stale=false` 时选择唯一作用域：文献与引用用 `paper`，路线、状态、计划与决策用 `project`，聚合运行指标与资源用 `experiment`，正文定位与表述用 `thesis`，明确跨域问题用 `all`。运行 `uv run --project scripts/literature_search --locked python -m scripts.literature_search query "查询" --scope <作用域> --mode hybrid --offline --json`。
4. 每条本地结果核对 `scope`、`collection`、`authority`、`status`、`evidence_level` 和原路径。`paper` 结果还必须核对 `paper_id`、`note_views`、`source_pdf`、`page_hint` 与 `evidence_block`；其他作用域不得按论文证据引用。研究判断答复须保留最小收据：`scope`、`mode`、索引 `manifest/hash` 或 `built_at`、`stale=false` 与关键命中路径。
5. `rg` 仅用于混合结果后的精确代码、行号和已知字面量核验，不能替代语义发现；问题从精确查找扩大为研究判断时必须回到本工作流重新路由。
6. 需要限定 collection 时重复使用 `--collection`；只有明确历史追溯才加 `--include-history`。
7. 只有论文本地结果不足、用户要求近期外部工作、源码、模型、数据集、Space 或 DOI/题录核验时，才移除 `--offline` 并使用 `--scope all`；项目、实验和正文查询默认不联网。
8. 在线结果单列为“未核全文候选”，同时报告各来源认证、缓存、延迟、限流、去重和失败状态。OpenAlex 缺密钥时只报告 `skipped_missing_key`，不把跳过写成普通搜索回退。
9. 若用户决定正式纳入外部候选，停止本技能并转入仓库规定的原件下载、全文核验和知识库写回流程。
10. 用户请求 Google Scholar 或学术搜索时调用 `$google-scholar`，程序化检索固定使用 `--json`，默认传统 `lookup`；只有既有认证或功能明确支持时才允许 `search`。需要源码语义核验时调用现有 `github:github` 技能；需要 HF 模型、数据集、Space 或论文关联时调用现有 `hf-cli`、`huggingface-papers`、`huggingface-datasets`。只读核验候选，不自动下载、登录、上传、索引或认领。

## 边界

- 不自动修改 `raw/`、`wiki/`、论文正文或 Zotero。
- 不索引 `INDEX.md`、归档、备份、缓存、依赖、运行大文件、检查点、逐样本预测、最终测试标签、原始大数组或疑似凭据内容；实验 JSON 只读取配置允许的文件名和字段。
- 不因在线 API 失败丢弃本地结果。
- 不把 OpenAlex、Semantic Scholar、Crossref、Hugging Face Papers 或 Google Scholar 的摘要、题录和搜索排序写成论文结论。Google Scholar 的 `clusterId`、引用数和排名只作发现元数据，候选固定标记为 `unverified_external_candidate`。
- Google Scholar 缺命令、缺认证、限流、验证码、超时或 JSON 错误时只记录来源降级，不以其他来源结果伪装成功，也不自动运行登录或 PDF 下载。
- 外部候选正式纳入必须继续执行 `raw/` 原件、`wiki/` 全文核验笔记和 Zotero 题录流程。
- GitHub `code_candidates` 与 HF `hub_candidates` 独立报告，不进入论文 RRF；普通搜索结果只能标为未核代码或 Hub 候选。
- 本机已有官方 GitHub 插件与 Hugging Face 技能，不安装来源和采用量更弱的第三方 GitHub 技能。
- 不根据负例查询的返回分数临时设置拒答阈值；可靠拒答门必须使用独立开发集冻结。
- 没有 `relevant_chunk_ids` 或 `relevant_chunk_keys` 时，不把相关笔记命中写成块级命中。
- `curated-regression-v1` 只作人工构造的开发/回归集，不得写成真实用户查询效果。
- `real-user-query-v1` 只作独立验收；相关性标注完成前不得查看或导出系统排名，也不得根据该集合调整 BM25、RRF 或阈值。
- 七篇文档等小样本构建只能称为“架构验证”，不能称为“全项目向量物化”；全量物化必须另有全部允许语料的构建收据。
- 向子代理委派可能输出研究判断的任务时，任务简报必须包含本技能的触发条件、作用域选择、陈旧索引处置与最小检索收据。
- 命令参数与重建方式以 `scripts/literature_search/README.md` 为准。
