# Claude Code 项目规则

@AGENTS.md

## Claude Code 适配说明

- 本文件是 Claude Code 的根级入口；`AGENTS.md` 是本仓库规则唯一来源，工具中立。
- 每个受管子目录的 `CLAUDE.md` 通过 `@AGENTS.md` 导入同目录 `AGENTS.md`。Claude Code 读取该目录内文件时，按目录级原生加载机制生效。
- 规则源 `AGENTS.md` 由 Codex 与 Claude Code 共享；基础设施（`.Codex/hooks/`、`.Codex/docs/`、`.Codex/tools/`）亦共享，各工具只在自己的配置文件里注册引用，不复制脚本。
- 用户明确要求与已发表参照协议对齐时，先完整核对原始全文的实际做法与证据强度；未经用户明确批准，不得自行叠加更严格的封印、额外独立测试或更高通过门。若路线合同将目标面板用于消融或方法选择，必须称为“目标知情评价面板”，如实披露目标标签参与选择，且不得称为独立最终测试、独立泛化确认、零回流或无偏最终估计。一般最终测试隔离仍只适用于真正被定义为独立最终测试的数据；目标知情评价不改变静态基础模型的训练标签边界。
- 实验制品的临时目录边界以 `AGENTS.md` 为准：`/tmp` 仅用于可丢弃中间产物，不得作为唯一可恢复制品。
- 新机制、新算法、新联合框架或新方向的构思/比较/筛选/裁决，依次实际使用 `research-ideation`、`source-command-sc-brainstorm`、`superpowers:brainstorming`，并保留 architectural HARD-GATE 与实验待证边界；常规启动不触发。
- 用户要求节省 Codex 额度、普通 ChatGPT、GitHub 交接或跨应用研究分工时，先读取仓库内 `chatgpt-handoff` Skill 与 `.Codex/docs/ChatGPT交接工作流.md`；仅限有界非执行任务，代码、服务器、GPU、Git 写入和制品核验仍由 Codex 完成，外部结果必须独立复核。
- 有已满足硬门的真实实验时，以实测吞吐、墙钟和有效并行避免 GPU 空闲，不以单个显存快照或机械占满显存判断；训练 batch 的语义变化须冻结前实测并在正式比较中共享，并发资源数据按 AGENTS.md 披露。
- 当两个代理的原生加载行为与 `AGENTS.md` 描述不同，以各自实际加载方式为准；研究边界、数据证据、凭据保护、验证和写入规则仍完整有效。
- 使用 `/memory` 核对本会话实际加载的 `CLAUDE.md` 与规则文件；规则是行为指引，权限、沙箱和工具限制以 Claude Code 设置为准。
- **文档目录约定**：本仓库过程文档（计划、笔记、审计、过程记录）放 `.Codex/docs/`（共享工作记忆，gitignored）；入库设计规约放 `.claude/docs/`。此约定覆盖全局规则中“`.claude/docs/`”的默认指向。
