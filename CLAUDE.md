# Claude Code 项目规则

@AGENTS.md

## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库规则唯一来源，工具中立。
- 每个受管子目录的 `CLAUDE.md` 通过 `@AGENTS.md` 导入同目录 `AGENTS.md`。Claude Code 读取该目录内文件时，按目录级原生加载机制生效。
- 规则源 `AGENTS.md` 由 Codex 与 Claude Code 共享；基础设施（`.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/`）亦共享，各工具只在自己的配置文件里注册引用，不复制脚本。
- 当两个代理的原生加载行为与 `AGENTS.md` 描述不同，以各自实际加载方式为准；研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
- 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件；规则是行为指引，权限、沙箱和工具限制以 Claude Code 设置为准。
- **文档目录约定**：本仓库过程文档（计划、笔记、审计、过程记录）放 `.Codex/docs/`（共享工作记忆，gitignored）；入库设计规约放 `.claude/docs/`。此约定覆盖全局规则中“`.claude/docs/`”的默认指向。
