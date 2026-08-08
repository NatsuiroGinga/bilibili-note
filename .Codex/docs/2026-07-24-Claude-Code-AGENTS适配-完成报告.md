# Claude Code 的 AGENTS 规则适配完成报告

## 结论

仓库现有的六级 `AGENTS.md` 已全部通过同级 `CLAUDE.md` 接入 Claude Code。根级过时说明已替换，不再与当前毕业论文研究规则冲突。

## 变更文件

- `CLAUDE.md`：导入根级 `AGENTS.md`，并增加 Claude Code 能力映射、规则加载和权限边界说明。
- `output/CLAUDE.md`
- `raw/CLAUDE.md`
- `thesis/CLAUDE.md`
- `thesis/experiments/llm_probe/CLAUDE.md`
- `wiki/CLAUDE.md`

五个子目录文件均只包含标题和 `@AGENTS.md` 导入，避免复制规则导致版本漂移。

## 验证

- `rg --files -g 'CLAUDE.md' -g 'AGENTS.md'`：确认六组同级规则文件齐全。
- `rg --line-number '^@AGENTS\\.md$' ...`：确认六个桥接文件均为第 3 行导入对应规则。
- 对每个桥接文件执行同级 `AGENTS.md` 存在性检查：全部通过。
- `git diff --check -- ...`：通过，无空白错误。
- `claude --version`：本机已安装 Claude Code `2.1.175`。

## 未修改内容

- 未改写六个原始 `AGENTS.md`。
- 未改动 `.claude/settings.json` 的权限配置。
- 未改动用户级 `/Users/bilibili/.claude/CLAUDE.md`；该文件已存在并会先于本仓库根级规则加载。

## 使用方式

从仓库根目录启动 Claude Code。进入或读取上述受管子目录时，Claude Code 会加载对应子目录的 `CLAUDE.md`，再导入同目录 `AGENTS.md`。可在会话中使用 `/memory` 查看实际加载结果。
