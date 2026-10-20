---
name: git-conventions
description: Git 提交与分支核心规范（精简常驻版，细则由 rule-injector hook 在 git 操作时注入）
---

# Git 核心规范（兜底条款）

- Commit/MR 标题：`type(scope): description`，Conventional Commits；description 英文、动词开头、首字母小写、无句号、每行 ≤72 字符
- **禁止 Co-Authored-By 署名**；项目 AGENTS.md 若要求 Assisted-by 署名行则按项目执行
- 分支命名 `{type}/{scope}-{description}`；禁止直接 push 开发主干，必须走 MR
- 完整提交格式、分支生命周期、MR 合并前防御检查清单：由 hook 在检测到 git commit/branch/push 等命令时自动注入（`~/.claude/hooks/rule-bundles/git-workflow.md`，可手动要求读取）
