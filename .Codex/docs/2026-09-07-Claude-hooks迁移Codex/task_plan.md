# Claude Code hooks 迁移到 Codex

## 目标

将 `~/.claude/settings.json` 的用户级 hooks 迁移到 `~/.codex/hooks.json`，复制依赖脚本到 `~/.codex/hooks/`，并按 Codex 当前事件、输入输出模式和信任机制适配。

## 执行状态

- [x] 读取根规则、过程文档规则、钩子开发规范与 Codex 官方 Hooks 文档。
- [x] 仅解析 Claude `settings.json` 的 `hooks` 字段并盘点依赖。
- [x] 读取现有 Codex 配置并确定无内联 `[hooks]` 配置。
- [x] 生成候选配置及适配脚本，完成 JSON 与脚本语法检查。
- [x] 备份原 `~/.codex/hooks.json` 并部署合并结果。
- [ ] 新会话中用 `/hooks` 审核并信任变更后的用户级 hooks。

## 文件边界

- 用户级配置：`~/.codex/hooks.json`
- 用户级脚本：`~/.codex/hooks/`
- 过程记录：本目录

## 验收

1. `jq empty ~/.codex/hooks.json` 通过。
2. 所有 JavaScript 脚本通过 `node --check`，启动脚本通过 `sh -n`。
3. 引用脚本和规则包均存在，配置没有 `prompt` 或 `agent` 类型处理器。
4. 下次 Codex 新会话中使用 `/hooks` 信任新增或变更的处理器。
