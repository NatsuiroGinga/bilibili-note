# 仓库外技能补丁说明

`rust-skills-complexity-resource.patch` 是完整的统一差异补丁，目标为：

- `/Users/bilibili/.codex/skills/daily-coding/SKILL.md`
- `/Users/bilibili/.codex/skills/rust-skills/SKILL.md`
- `/Users/bilibili/.codex/skills/rust-skills/rules/perf-stream-state-bound.md`
- `/Users/bilibili/.codex/skills/rust-skills/rules/perf-production-resource-budget.md`

未直接修改上述仓库外文件。`skill-improver` 的备份脚本在创建 `/Users/bilibili/.codex/skills/backup/` 时被权限拒绝，因此不能满足其“先备份再更新”前提。可在具备该目录写权限后执行 `patch -p0 < rust-skills-complexity-resource.patch`，然后执行 `verify-update.sh`；本任务按约束未运行该脚本。
