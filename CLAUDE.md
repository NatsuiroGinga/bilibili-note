# Claude Code 项目规则

@AGENTS.md

## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库规则唯一来源，工具中立。
- 每个受管子目录的 `CLAUDE.md` 通过 `@AGENTS.md` 导入同目录 `AGENTS.md`。Claude Code 读取该目录内文件时，按目录级原生加载机制生效。
- 规则源 `AGENTS.md` 由 Codex 与 Claude Code 共享；基础设施（`.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/`）亦共享，各工具只在自己的配置文件里注册引用，不复制脚本。
- 实验制品的临时目录边界以 `AGENTS.md` 为准：`/tmp` 仅用于可丢弃中间产物，不得作为唯一可恢复制品。
- 新机制、新算法、新联合框架或新方向的构思/比较/筛选/裁决，依次实际使用 `research-ideation`、`source-command-sc-brainstorm`、`superpowers:brainstorming`，并保留 architectural HARD-GATE 与实验待证边界；常规启动不触发。
- 普通 ChatGPT 只读交接规则见 `.Codex/docs/ChatGPT交接工作流.md`：仅限有界非执行任务，代码、服务器、GPU、Git 写入和制品核验仍由 Codex 完成，外部结果必须独立复核。
- 当两个代理的原生加载行为与 `AGENTS.md` 描述不同，以各自实际加载方式为准；研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
- 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件；规则是行为指引，权限、沙箱和工具限制以 Claude Code 设置为准。
- **文档目录约定**：本仓库过程文档（计划、笔记、审计、过程记录）放 `.Codex/docs/`（共享工作记忆，gitignored）；入库设计规约放 `.claude/docs/`。此约定覆盖全局规则中“`.claude/docs/`”的默认指向。
