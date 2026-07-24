# Claude Code 迁移配置检查记录

## 检查范围

- 仓库：`CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`
- 用户级 Codex：`/Users/bilibili/.codex/config.toml`
- 运行时：`codex --strict-config doctor`、`codex mcp list`

## 已确认事实

- `AGENTS.md` 与 `CLAUDE.md` 仅有 3 处标题/产品名称替换，正文规则一致。
- `.claude/settings.json` 是合法 JSON，包含 2 条 Claude Code 的 Bash 命令许可。
- `cp` 与 `pdftotext` 已安装；下载目录中的源 PDF 存在。
- PDF 当前实际位置为 `raw/papers/attack-detection/2504.13592v2.pdf`，而设置中 `pdftotext` 使用的 `raw/papers/2504.13592v2.pdf` 不存在。
- Codex 0.144.4 可加载 `config.toml`，严格配置诊断通过；该仓库被识别为 `~/personal/note`。
- 已启用 `claude-plugins-official` 市场及其 `github`、`gopls-lsp`、`superpowers` 插件。

## 运行时告警

- GitLab MCP 无法连接。
- OpenAI 端点与 WebSocket 的 DNS/HTTP 连通性检查失败；同时检测到 ChatGPT 登录与 API 密钥环境变量并存。
- 每次调用 CLI 出现“无法创建 PATH 别名”的受限环境警告；该问题发生在当前受限执行环境中。

## 兼容性判断

- `AGENTS.md` 可作为 Codex 的仓库指令文件。
- `.claude/settings.json` 是 Claude Code 专用设置，Codex 不会自动采用其中的 Bash 许可规则。
