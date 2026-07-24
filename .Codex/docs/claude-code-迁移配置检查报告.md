# Claude Code 迁移配置检查报告

## 结论

迁移并非完全正常：仓库指令迁移已完成并保持一致，但 Claude Code 的命令许可仍留在 `.claude/settings.json`，不会自动作用于 Codex；其中一条 PDF 路径也已经失效。Codex 主配置可以解析和加载，但 GitLab MCP 与模型服务连通性尚未通过诊断。

## 检查范围

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`
- `/Users/bilibili/.codex/config.toml`
- `codex --strict-config doctor`
- `codex mcp list`

## 检查结果

| 项目            | 结果           | 证据                                                                                                |
| --------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| 项目说明迁移    | 通过           | `AGENTS.md` 与 `CLAUDE.md` 仅有 3 处面向产品的名称替换，项目规则正文一致。                          |
| Claude 设置语法 | 通过           | `.claude/settings.json` 可被 `jq empty` 成功解析。                                                  |
| Claude 命令许可 | 不适用于 Codex | 配置格式为 Claude Code 的 `permissions.allow`；Codex 使用自身的沙箱和审批策略。                     |
| PDF 许可路径    | 失败           | 配置引用 `raw/papers/2504.13592v2.pdf`，实际文件在 `raw/papers/attack-detection/2504.13592v2.pdf`。 |
| Codex 主配置    | 通过           | `codex --strict-config doctor` 显示 `config.toml parse ok`，仓库路径被正确识别。                    |
| Claude 插件迁移 | 通过           | `claude-plugins-official` 市场已配置，`github`、`gopls-lsp`、`superpowers` 插件已启用。             |
| MCP 可用性      | 未完全通过     | GitLab MCP 连接超时；其余服务器的状态由诊断列为可选问题或不支持认证状态。                           |
| 模型服务连通性  | 未完全通过     | 诊断发现 WebSocket 的 DNS 失败，且 API 密钥模式下 HTTP 端点不可达。                                 |

## 建议处理顺序

1. 修正或删除 `.claude/settings.json` 中失效的 `pdftotext` 路径；若已改用 Codex，可直接移除该文件中的 Claude Code 专用许可。
2. 确认是否需要 GitLab MCP；需要则检查公司网络、VPN、DNS 与 GitLab 服务地址，不需要则在 Codex 配置中禁用。
3. 统一认证方式：保留 ChatGPT 登录或 API 密钥中的一种，并确认相关端点能被当前网络解析。
4. 将 `AGENTS.md` 纳入版本控制，确保其他工作副本同样获得仓库规则。

## 未修改内容

本次未修改 `CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`、`/Users/bilibili/.codex/config.toml` 或任何 MCP/认证配置。
