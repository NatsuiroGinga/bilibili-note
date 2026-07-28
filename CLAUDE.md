# Claude Code 项目规则

@AGENTS.md

## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库与其他编码代理共用的项目规则唯一来源。
- 每个受管子目录的 `CLAUDE.md` 都导入同目录的 `AGENTS.md`。Claude Code 读取该目录内文件时，会按需加载该目录规则。
- `AGENTS.md` 中出现的 Codex 专属工具名、技能名、代理名、配置名或斜杠命令，应遵循其安全与质量目标，并只使用当前 Claude Code 实际可用的等效能力；不得假定不存在的命令或工具。
- 当 Claude Code 的原生规则加载行为与 `AGENTS.md` 的 Codex 机制描述不同，以 Claude Code 的实际加载方式为准；研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
- 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件；规则是行为指引，权限、沙箱和工具限制以 Claude Code 设置为准。
