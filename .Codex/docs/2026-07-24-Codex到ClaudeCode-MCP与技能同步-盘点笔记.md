# Codex 到 Claude Code 的 MCP 与技能同步盘点笔记

## 安全原则

- 不在本文档、终端输出或仓库中记录令牌、密码、Cookie 或认证头实际值。
- 用户级 MCP 配置写入 `~/.claude.json`；项目文件 `.mcp.json` 不用于本次同步。

## 初步信息

- Codex MCP 服务器名：`node_repl`、`computer-use`、`GitLab`、`ast-grep`、`huggingface`、`github`、`zotero`。
- Claude Code 官方支持用户级 MCP、项目级 `.mcp.json` 和环境变量展开；同名服务器按作用域优先级去重。
- Claude Code 的全局技能目录为 `~/.claude/skills/`，与 Codex 的 `~/.codex/skills/` 分离。

## 安全映射

| Codex 项目 | 处理方式 | 原因 |
| --- | --- | --- |
| `GitLab` MCP | 同步为 Claude Code 用户级 HTTP MCP | 使用 `${GITLAB_TOKEN}`，不复制令牌。 |
| `ast-grep` MCP | 同步为 Claude Code 用户级 stdio MCP | `npx` 已可用，配置不含凭据。 |
| `mcpmarket-me` MCP | 同步为 Claude Code 用户级 HTTP MCP | Codex 中已启用，配置不含凭据。 |
| `github`、`huggingface` MCP | 保留 Claude Code 现有项 | 当前已存在同类连接；不创建重复定义。 |
| `zotero` MCP | 暂不写入 | 当前 shell 未提供其必需环境变量；不得复制 Codex 中的密钥。 |
| `node_repl`、`computer-use` MCP | 不同步 | 前者依赖 Codex 应用内部运行时，后者在 Codex 中已禁用。 |
| `git-commit`、`git-push` 技能 | 复制到 `~/.claude/skills/` | 仅包含通用 Git 工作流文本，无 Codex 运行时依赖。 |
| `session-wrap-up` 技能 | 不同步 | 包含 Codex 钩子模拟脚本调用。 |
| Codex `.system` 技能 | 不同步 | 依赖 Codex 专属工具或安装机制。 |
| `web-design-reviewer` | 不覆盖 | Claude Code 中已存在被显式禁用的版本。 |

## 验证结果

- `git-commit` 与 `git-push` 已复制到 `~/.claude/skills/`，并与 Codex 源文件逐字节一致。
- Claude Code 在非沙箱网络环境中确认 `ast-grep` 已连接。
- `mcpmarket-me` 已保存定义，但需要在 Claude Code 的 `/mcp` 中完成认证。
- GitLab、新旧 GitHub 与 Hugging Face 在健康检查中未连接。此结果不改变已保存的配置；GitLab 需要确认企业网络或 VPN，GitHub 与 Hugging Face 为同步前已存在的失败项。
