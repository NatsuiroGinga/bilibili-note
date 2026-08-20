# Google Scholar 混合检索接入计划

## 目标

将 Google Scholar 作为本地混合文献检索的外部论文候选来源，并保持本地全文证据、外部候选、代码候选和 Hub 候选之间的既有隔离。

## 文件范围

- `scripts/literature_search/online.py`
- `scripts/literature_search/README.md`
- `AGENTS.md`
- `.agents/skills/literature-hybrid-search/SKILL.md`
- `.Codex/docs/2026-08-20-GoogleScholar混合检索接入/task_plan.md`
- `.Codex/docs/2026-08-20-GoogleScholar混合检索接入/notes.md`
- `.Codex/docs/2026-08-20-GoogleScholar混合检索接入/实施报告.md`

## 实施步骤

- [x] 完整读取仓库规则、局部规则、Google Scholar 技能、既有 GitHub/HF 实现与报告。
- [x] 核对 `scholar` 命令、域知识文件和修改前 Git 状态。
- [x] 实现 Scholar CLI 来源、JSON 解析、失败降级和论文候选合并。
- [x] 更新根路由、混合检索技能和使用文档。
- [x] 执行一次最小编译、导入、CLI、离线与可行的真实来源查询验证。
- [x] 记录实施报告并检查共享暂存区；仅在暂存区为空时提交精确文件。

## 冻结接口

- Google Scholar 仅作为 `online.paper_candidates` 和兼容字段 `online.results` 的论文来源，不进入本地全文 RRF。
- 程序只用参数列表调用 `scholar`，不使用 shell；机器处理固定请求 JSON。
- 默认使用传统 `lookup`。仅在显式配置且可用时使用 `search`，状态必须如实记录命令模式。
- 缺命令、缺认证、验证码、限流、超时、非零退出和 JSON 错误均降级为 Google Scholar 单来源失败。
- 所有 Scholar 命中标记 `unverified_external_candidate`；引用数、聚类标识和排名仅是发现元数据。
- 离线时标记 `skipped_offline`；`scope=local` 不进入在线发现函数。
- 不下载 PDF，不修改 `raw/`、`wiki/`、Zotero 或论文正文，不执行登录交互。

## 验收命令

- `uv run --project scripts/literature_search --locked --no-sync python -m compileall -q -x '/\\.venv/' scripts/literature_search`
- `uv run --project scripts/literature_search --locked --no-sync python -c 'from scripts.literature_search.online import search_google_scholar; print("导入通过")'`
- `uv run --project scripts/literature_search --locked --no-sync python -m scripts.literature_search query --help`
- `uv run --project scripts/literature_search --locked --no-sync python -m scripts.literature_search query 'normality shift' --scope all --mode lexical --top-k 2 --index .cache/literature-search/p0-full.sqlite3 --offline --json`
- 若 `scholar` 可用且认证允许：以公开通用主题执行一次来源级 JSON 查询；否则记录精确阻塞。

## 阻塞条件

- 当前 `PATH` 中没有 `scholar` 命令。
- Google Scholar 技能目录中没有 `domain-knowledge.local.md`。
- 若提交前共享暂存区非空，禁止提交并向控制器报告。

## 状态

任务已完成。功能提交为 `03982e4`；真实 Scholar 网络响应因命令缺失而未发生。
