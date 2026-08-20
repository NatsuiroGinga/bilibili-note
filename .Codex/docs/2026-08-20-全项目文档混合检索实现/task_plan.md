# 全项目文档混合检索实施计划

## 目标

在保持默认论文检索语义和论文身份去重合同的前提下，将活动项目文档、精选实验收据和论文正文纳入单一 SQLite 多 collection 索引，提供 `paper/project/experiment/thesis/all` 作用域隔离。

## 边界

- 只修改 `scripts/literature_search/`、根 `AGENTS.md`、`.agents/skills/literature-hybrid-search/SKILL.md` 和本实施目录。
- 不覆盖、回滚、暂存或提交其他代理的现有改动。
- 不引入近似最近邻；继续使用 SQLite FTS5、E5 和 NumPy 精确点积。
- 不索引 `INDEX.md`、归档、备份、缓存、依赖、模型权重、检查点、逐样本预测、最终测试标签、原始大数组或疑似凭据内容。
- 实验收据只通过文件名允许清单和字段允许清单提取聚合事实，不转储原始 JSON。

## 实施阶段

- [x] 阶段一：读取规则、技能、审计提交与当前实现，记录工作树并行改动。
- [x] 阶段二：冻结通用文档、collection、权威、状态、证据和敏感度元数据合同。
- [x] 阶段三：实现安全扫描、类型化分块、单库模式、增量复用和 collection 陈旧收据。
- [x] 阶段四：实现 `paper/project/experiment/thesis/all` 路由、collection 过滤、分区输出与论文证据隔离。
- [x] 阶段五：更新 README、根触发规则和混合检索技能。
- [x] 阶段六：执行一次最小编译、导入、CLI、真实小规模构建和作用域查询，记录语料、大小与延迟。
- [x] 阶段七：检查共享暂存区，仅在为空时提交本任务独占文件。

## 验收命令

```bash
python3 -m compileall -q scripts/literature_search
python3 -c 'import scripts.literature_search.cli; import scripts.literature_search.documents; import scripts.literature_search.search'
python3 -m scripts.literature_search --help
python3 -m scripts.literature_search build --lexical-only --repo-root <小规模真实仓库镜像> --index <临时索引> --json
python3 -m scripts.literature_search query "<真实查询>" --repo-root <小规模真实仓库镜像> --index <临时索引> --mode lexical --scope <作用域> --json
```

## 决策

- 任务简报明确要求“单一 SQLite 多 collection”，晚于审计文档的“论文库加项目库”建议；本轮按较新明确约束实施单库，但以 collection 保留治理隔离。
- `local` 作为 `paper` 的兼容别名保留；新默认作用域显式为 `paper`。
- 不修改已有未提交的 `embeddings.py`、`lexical.py`、`.gitignore` 和依赖迁移改动。

## 错误与阻塞

- 当前工作树存在其他代理的未提交改动；通过限定文件范围和提交前共享暂存区检查避免混入。
- README 首次多文件补丁因段落上下文不匹配而整体未应用；改为按当前精确段落分批修改后成功。
- 首次 `compileall` 误递归进入局部 `.venv`，且系统字节码缓存目录不可写；改用显式 `*.py` 清单和 `/tmp` 字节码缓存后通过。
- 首次 `uv run` 因用户缓存目录不可写而未进入项目代码；将 `UV_CACHE_DIR` 指向 `/tmp` 后导入成功。

## 状态

**已完成**：实现、文档、真实构建、增量收据、作用域隔离和敏感排除均已验证，待提交本任务独占文件。
