# GitHub 代码候选检索通道实施计划

## 目标

在现有本地论文证据与在线论文候选之外，新增 GitHub 仓库代码候选通道。GitHub 结果独立输出为 `code_candidates`，不进入本地论文 RRF、在线论文 `results` 或论文证据等级。

## 文件范围

- `scripts/literature_search/online.py`
- 必要时最小修改 `scripts/literature_search/config.py`、`config.json`、`cli.py`、`README.md`
- `.agents/skills/literature-hybrid-search/SKILL.md`
- `.Codex/docs/2026-08-20-GitHub代码候选检索实施报告.md`

禁止修改向量、词法、RRF、索引模式、论文笔记、原件、Zotero 和实验。

## 接口合同

1. 使用 GitHub REST `GET /search/repositories`，可选从环境读取 `GITHUB_TOKEN` 并通过请求头认证；任何输出、错误和缓存均不得包含令牌。
2. 无令牌允许公共低配额查询，状态记录 `authenticated=false`、速率限制、延迟、HTTP 状态、退避和降级原因。
3. 每项输出规范仓库 URL、`owner/name`、描述、主页、许可证、星数、归档状态、更新时间、默认分支、匹配依据和核验状态。
4. 普通搜索命中固定为 `unverified_code_candidate`。本工具不根据名称相似度自动升级论文代码关联。
5. 按规范仓库 URL 去重。GitHub 403/429 或限流响应只在提供有效 `Retry-After` 时最多重试一次，不盲重试。
6. `discover_online` 保留现有论文 `results` 和 `provider_status` 兼容字段，新增独立 `code_candidates` 与 GitHub provider 状态；`scope=all` 继续分区输出本地论文、在线论文和代码候选。

## 验证

1. 核验 GitHub 官方仓库搜索、认证、速率限制和许可证字段文档。
2. Python 编译、模块导入、CLI 帮助与 README/技能路径检查各一次。
3. 使用 `GRANDE` 和 `RWKV` 各执行一条真实联网查询，记录认证、限流、结果结构和 URL 去重。
4. 验证 GitHub 失败或离线时，本地论文结果仍保留，在线论文候选字段保持兼容。
5. 不运行 `black`，不创建向量索引或训练任务。

## 状态

- [ ] 官方接口核验
- [ ] 实现独立 GitHub 通道
- [ ] 真实联网验证
- [ ] 报告与提交
