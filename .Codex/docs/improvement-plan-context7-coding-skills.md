# Context7 编码技能改进计划

## 高优先级

### 1. `daily-coding` 增加第三方 API 新鲜度门禁

- **目标文件**：`/Users/bilibili/.codex/skills/daily-coding/SKILL.md`
- **问题**：当前技能未要求在第三方库、版本敏感接口或不确定 API 上核验当前文档，可能生成过时或不存在的调用。
- **修改**：在“开始前”加入条件式 Context7 规则。先从项目清单或锁文件确定库与版本；涉及第三方库且接口不确定、版本敏感或首次使用时必须查询 Context7。标准库、仓库内已有且已编译的相同接口不重复查询。Context7 不可用时退回对应版本的官方文档或本地安装源码，不得凭记忆猜测。

### 2. `rust-skills` 增加 crate 版本与特性核验门禁

- **目标文件**：`/Users/bilibili/.codex/skills/rust-skills/SKILL.md`
- **问题**：当前技能包含 Rust 语言和工程规则，但未约束第三方 crate API 的版本新鲜度与 Cargo 特性标志。
- **修改**：新增“Context7 与 crate API 新鲜度”章节。使用第三方 crate 的新接口、版本敏感接口或不确定符号前，先从 `Cargo.toml`/`Cargo.lock` 确定精确版本和特性，再用 Context7 核验；标准库、仓库内部模块和现有可编译同构调用不查询。不可用时只采用对应版本官方文档、`docs.rs` 或本地 crate 源码。

## 中优先级

- 两个技能都要求只在实际触发门禁时，在实施报告记录库名、版本、核验来源和采用的 API；禁止为了形式对每次编码都调用 Context7。
- 保持原 YAML 前置元数据、现有规则编号和引用结构不变。

## 验证

1. 使用 `skill-improver/scripts/backup-skill.sh` 分别备份两个技能。
2. 应用修改后使用 `skill-improver/scripts/verify-update.sh` 分别验证。
3. 使用 `rg` 确认两个技能均包含 Context7 条件触发、免触发条件和不可用时的回退路径。
4. 生成 `.Codex/docs/update-report-context7-coding-skills-20260811.md`。
