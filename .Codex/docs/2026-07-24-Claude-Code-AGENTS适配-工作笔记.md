# Claude Code 的 AGENTS 规则适配工作笔记

## 已核验事实

- Claude Code 官方文档明确说明：它读取 `CLAUDE.md`，而不是 `AGENTS.md`。
- 官方推荐在 `CLAUDE.md` 中写入 `@AGENTS.md`，以便复用跨代理规则；子目录中的 `CLAUDE.md` 会在读取该目录文件时按需加载。
- 仓库当前有 1 个根级 `AGENTS.md`、5 个受管子目录 `AGENTS.md`，以及 1 个已过期的根级 `CLAUDE.md`。
- 旧根级 `CLAUDE.md` 将仓库描述为 Bilibili 运维知识库；根级 `AGENTS.md` 将当前主线定义为恶意流量检测毕业论文。二者冲突。

## 来源

- Claude Code 官方文档：<https://code.claude.com/docs/zh-CN/memory>
- 当前仓库规则：`AGENTS.md`、`output/AGENTS.md`、`raw/AGENTS.md`、`thesis/AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`wiki/AGENTS.md`。
