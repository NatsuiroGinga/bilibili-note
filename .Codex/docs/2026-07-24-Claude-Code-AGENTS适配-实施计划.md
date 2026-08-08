# Claude Code 的 AGENTS 规则适配实施计划

## 目标

让 Claude Code 在仓库根目录及五个受管子目录中，自动加载对应的既有 `AGENTS.md`，并消除根级旧 `CLAUDE.md` 与当前论文研究规则的冲突。

## 范围与边界

- 修改根级 `CLAUDE.md`，保留为 Claude Code 的入口和适配层。
- 新建五个子目录的 `CLAUDE.md`，仅桥接其同目录 `AGENTS.md`。
- 不改写任何 `AGENTS.md` 的研究规则，不修改 `.claude/settings.json` 的命令许可。
- 不写入或复制任何凭据。

## 阶段

- [x] 阶段 1：核对 Claude Code 官方加载机制、现有规则层级和旧入口冲突。
- [x] 阶段 2：建立根级与子目录的 `CLAUDE.md` 桥接文件。
- [x] 阶段 3：验证导入路径、层级覆盖和 Markdown 格式；记录交付结果。

## 决策

- 使用 `@AGENTS.md` 导入，而非符号链接：它允许在根级保留 Claude Code 专用的解释层，并避免不同平台的符号链接差异。
- 根级 `CLAUDE.md` 以当前 `AGENTS.md` 为唯一项目规则来源：现有内容把仓库描述为旧的 Obsidian 运维笔记库，与当前论文研究主线相冲突。
- 子目录只放最小桥接内容，以免复制、漂移或覆盖现有分层规则。

## 验收命令

- `rg --files -g 'CLAUDE.md' -g 'AGENTS.md'`
- `rg --line-number '^@AGENTS\\.md$' CLAUDE.md output/CLAUDE.md raw/CLAUDE.md thesis/CLAUDE.md thesis/experiments/llm_probe/CLAUDE.md wiki/CLAUDE.md`
- `git diff --check -- CLAUDE.md output/CLAUDE.md raw/CLAUDE.md thesis/CLAUDE.md thesis/experiments/llm_probe/CLAUDE.md wiki/CLAUDE.md`

## 状态

**已完成。** 六个 `CLAUDE.md` 均已指向对应 `AGENTS.md`；导入路径检查、文件存在性检查和 `git diff --check` 均通过。已确认本机 Claude Code 版本为 `2.1.175`。
