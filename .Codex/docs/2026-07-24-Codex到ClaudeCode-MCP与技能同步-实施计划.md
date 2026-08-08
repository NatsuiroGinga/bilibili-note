# Codex 到 Claude Code 的 MCP 与技能同步实施计划

## 目标

将当前用户可复用的 Codex MCP 服务器和技能同步到 Claude Code，同时保留 Claude Code 已有配置、避免复制凭据，并验证加载结果。

## 边界

- MCP 使用 Claude Code 的用户级配置，避免将个人工具与认证信息提交进仓库。
- 只同步定义可安全映射的服务器；凭据继续通过既有环境变量、OAuth 或 Claude Code 的安全存储提供。
- 技能仅同步 Codex 专属、Claude Code 尚未拥有且不依赖 Codex 运行时的项目；不覆盖 Claude Code 已有同名技能。
- 不删除 Codex 配置、Claude Code 配置或任何技能目录。

## 阶段

- [x] 阶段 1：盘点双方的 MCP、技能、作用域与重复项。
- [x] 阶段 2：生成安全映射，标记不可迁移项和需要认证的项。
- [x] 阶段 3：写入 Claude Code 用户级配置并复制必要技能。
- [x] 阶段 4：验证 Claude Code 列表与技能发现结果，记录差异。

## 当前状态

**已完成。** 已新增 3 个用户级 MCP，并同步 2 个兼容技能；ast-grep 已连接，GitLab、mcpmarket-me 和既有 GitHub、Hugging Face 仍需认证或网络恢复。

## 盘点错误

- 首次按假定的顶层路径读取部分 Codex 系统技能失败；后续已确认它们位于 `~/.codex/skills/.system/`，属于 Codex 专属运行时，不同步到 Claude Code。
- 首次调用 `claude mcp add` 时，`--header` 的可变参数吞并了服务器名，命令在写入前报“缺少 name”。后续改用 `--header=...`，以固定选项边界。
