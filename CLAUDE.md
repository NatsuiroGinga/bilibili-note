# Claude Code 项目规则

@AGENTS.md

## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库唯一规则源，通过上方导入自动同步，禁止复制整份规则正文。
- 每个受管子目录的 `CLAUDE.md` 同样通过 `@AGENTS.md` 导入同目录规则；Claude Code 按目录级原生加载机制读取。
- `AGENTS.md` 中的 Sol／Astra／Terra／Luna 职责链在 Claude Code 中按当前可用模型能力映射；无法逐次设置 `effort` 时如实记录会话或代理定义提供的强度，不得声称提示词中的强度已经生效。
- Codex 与 Claude Code 共享 `.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/` 等基础设施，各工具只在自身配置中注册入口，不复制脚本。
- 两个工具的原生加载行为不同时，以各自实际行为为准；研究边界、数据证据、凭据保护、验证和文件职责仍以 `AGENTS.md` 为准。
- 使用 `/memory` 核对本会话实际加载的规则。文档落点按 `AGENTS.md` 的生命周期分流判据执行，不在本文件另设目录规则。
