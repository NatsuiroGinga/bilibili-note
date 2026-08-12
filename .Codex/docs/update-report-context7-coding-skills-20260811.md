# Context7 编码技能更新报告

## 摘要

- 更新日期：2026-08-11
- 改进计划：`.Codex/docs/improvement-plan-context7-coding-skills.md`
- 修改技能：`daily-coding`、`rust-skills`
- 修改范围：仅修改两个技能的 `SKILL.md`，未修改规则文件、脚本或其他技能。

## 已应用修改

### `daily-coding`

- 在“开始前”加入第三方 API 新鲜度门禁：先从项目清单或锁文件确定库名、版本和特性；首次使用、版本敏感或 API 不确定时必须查询 Context7。
- 明确免触发条件：标准库、仓库内部模块和已有编译通过的同构调用不重复查询。
- 明确回退路径：Context7 不可用时只使用对应版本官方文档或本地安装源码。
- 仅在实际触发门禁时记录库名、版本、来源和采用接口。

### `rust-skills`

- 新增“Context7 与 crate API 新鲜度”章节。
- 要求从 `Cargo.toml` 与 `Cargo.lock` 确定精确 crate 版本和特性标志后再查询 Context7。
- 明确标准库、仓库内部模块和同锁定版本下已有可编译调用不触发查询。
- 明确 Context7 不替代 `cargo check`、编译器诊断或真实运行。

## 备份

- `/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/`
- `/Users/bilibili/.codex/skills/backup/rust-skills-20260811-112930/`

备份文件数分别为 `1` 和 `283`。

## 验证

- 两个目标 `SKILL.md` 均存在。
- 当前技能文件与经审阅的暂存副本逐文件一致。
- 使用 `rg` 确认两个技能均包含：Context7 条件触发、免触发条件、不可用回退和实施报告记录要求。
- 使用 `fd` 确认两个备份目录包含预期文件。
- YAML 前置元数据未修改；`name` 与 `description` 仍存在。
- 未运行 `skill-improver/scripts/verify-update.sh`：该脚本内部使用仓库规则明确禁止的 `find`、`grep` 和 `sed`。已使用 `rg`、`fd`、`cmp` 与文件存在性检查完成等价验证。

## 当前状态

`UPDATE=COMPLETE`

后续编码代理只有在第三方 API 版本敏感或不确定时才调用 Context7，不会因形式要求拖慢普通编码。
