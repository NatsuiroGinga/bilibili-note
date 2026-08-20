# 本地文献混合检索效果评估笔记

## 任务边界

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`。
- 执行代理：`literature_hybrid_search_eval_sol_high`。
- 模型：`gpt-5.6-sol`，`effort=high`。
- 只提交本目录；不修改或暂存其他代理在 `scripts/literature_search/` 中的生产代码变更。

## 已读规则与资料

- 根 `AGENTS.md`。
- `.Codex/docs/AGENTS.md`。
- `.Codex/docs/2026-08-19-关键词向量混合文献检索/task_plan.md`。
- `.Codex/docs/2026-08-19-关键词向量混合文献检索/notes.md`。
- `.Codex/docs/2026-08-19-关键词向量混合文献检索/实施计划.md`。
- `scripts/literature_search/README.md`。
- `.agents/skills/literature-hybrid-search/SKILL.md`。
- `planning-with-files`、`results-analysis`、`expression-skill` 和 `using-superpowers` 技能说明。

## 已知状态

- `scripts/literature_search/` 有其他代理的未提交变更，包含新建 uv 项目与评估入口。
- 既有设计索引 507 篇 `wiki/papers/**/*.md`，向量模型为固定修订的 `intfloat/multilingual-e5-small`。
- 评估必须离线运行，不允许新模型或新权重进入冻结环境。

## 索引状态与离线重建

- 重建前默认索引：`stale=true`，511 篇笔记、6854 个分块、6854 个向量、384 维、CPU，37,617,664 字节；旧构建墙钟 348.798 秒。
- 为避免与其他代理争用默认索引，用同一生产配置构建独立评估索引 `.cache/literature-search/eval-index.sqlite3`。
- 重建命令：`UV_CACHE_DIR=.cache/uv-eval UV_OFFLINE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --project scripts/literature_search --locked python -m scripts.literature_search build --index .cache/literature-search/eval-index.sqlite3 --model-cache .cache/literature-search/model-cache --offline --device cpu --json`。
- 新索引：构建时间 `2026-08-20T09:33:48.006252+00:00`，墙钟 261.139 秒，512 篇笔记、6866 个分块、6866 个向量、384 维、CPU，38,301,696 字节。
- 模型：`intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3`，仅读现有 `.cache/literature-search/model-cache/`，无设备回退。
- 来源清单哈希：`09fd391dd637ef80406d6b1158a71992f43e4699a4d5036b226e475a0b7d9f24`。重建后立即运行 `status --index .cache/literature-search/eval-index.sqlite3 --json`，结果 `stale=false`。
- 旧索引与新索引的笔记计数相差 1、分块相差 12；本评估的冻结输入以上述新哈希为准。

### 并发变化与最终稳定快照

- 首轮评测后，`status` 将评估索引重新判为 `stale=true`。只读 Git 状态定位到其他任务新增 `wiki/papers/methodology/2023-Jiang-ForkMerge辅助任务负迁移.md` 且修改 `wiki/papers/methodology/INDEX.md`。
- 该任务确认写入冻结后，本评估重建 `.cache/literature-search/eval-final-index.sqlite3`：`built_at=2026-08-20T09:48:00.510876+00:00`，`build_seconds=203.660`，哈希 `d1f60a17a4fedbbdd1148bdec87536863b671fc1ca87d2957e5483d190f07947`，512 篇笔记、6866 分块/向量、384 维、38,297,600 字节，CPU，`stale=false`。
- 最终索引上复跑 16×3 个查询—模式组合，所有相关排名与首轮一致；`raw_results.json` 与 `metrics.json` 已覆盖为最终快照结果。

## 方法记录

- 查询集先于实际评测冻结。
- 多相关文档查询用 `Recall@k`；一个查询的倒数排名只由第一个相关结果计算，再对非负例查询求平均得 `MRR@10`。
- 无结果负例不纳入 `Recall` 和 `MRR` 分母，单独检查是否返回伪相关结果以及工具是否提供“无可信命中”语义。
- 延迟是单台本机的墙钟诊断，将注明设备、冷启动或热查询条件，不推广到其他环境。

## 错误记录

- 首次运行评估驱动在导入阶段失败：`ModuleNotFoundError: No module named 'scripts'`，尚未执行任何冻结查询。
- 根因：以文件路径执行时，Python 将评估目录而非仓库根加入 `sys.path`；同一虚拟环境在仓库根执行 `python -c 'import scripts'` 可成功，确认依赖已安装且故障在模块搜索路径。
- 单一修复：评估驱动从自身绝对路径计算仓库根，再导入生产包；不修改检索逻辑或环境。

## 外部方法检索

- 本轮未执行外部检索。`Recall@k` 与 `MRR` 的口径可由本任务评估合同完整定义，无需为扩大范围引入新外部材料。索引构建与评测全程保持离线。

## 最终指标摘要

| 模式 | 宏平均 Recall@5 | 宏平均 Recall@10 | MRR@10 | 中位延迟 |
| --- | ---: | ---: | ---: | ---: |
| lexical | 0.9405 | 0.9762 | 0.7619 | 21.59 ms |
| vector | 0.9048 | 0.9762 | 0.8214 | 42.96 ms |
| hybrid | 0.9762 | 0.9762 | 0.8631 | 65.21 ms |

- 两个负例的三种模式均未拒答。
- 混合 Top-10 相关命中对为 16；`source_pdf` 非空 16，原件实际存在 6，`page_hint` 非空 8。
- 空模型缓存下，离线词法查询退出码 0 且有结果；离线向量查询退出码 2，明确失败且不静默降级。

## 待办

- [x] 核验 uv 环境、模型缓存和索引陈旧状态。
- [x] 阅读评估入口和现有冻结查询，但不直接把现有检索输出当真值。
- [x] 从任务证据矩阵和全文笔记冻结 16 条查询及相关路径。
- [x] 运行三模式评估、功能门禁和逐查询分析。
- [x] 编写 `评估报告.md`并保留原始结果与聚合指标。
