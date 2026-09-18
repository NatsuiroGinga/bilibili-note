【按需注入·Git 提交与分支规范】本条规则被 hook 检测到 git 提交/分支操作时注入，仅约束本次相关动作。

提交信息（Conventional Commits）：
- 格式 `type(scope): description`；type ∈ feat/fix/refactor/docs/chore/test/revert
- description 必须英文、动词开头、首字母小写、末尾无句号；每行 ≤72 字符；body 可中文说明背景原因
- revert 必须注明被回滚的 commit hash
- 禁止任何 Co-Authored-By 署名；若项目 AGENTS.md 要求 Assisted-by 署名行则按项目规范执行

分支与交付：
- 分支命名 `{type}/{scope}-{description}`，type ∈ feature(≤2周)/fix(≤3天)/hotfix(≤1天)/refactor(≤1周)/chore(≤3天)/exp
- 禁止直接 push 开发主干，必须经 MR；MR 标题同 commit 格式
- 交付前检查：测试通过、类型检查无报错、已 rebase 最新主干、无调试残留（print/breakpoint/临时 TODO 注释）、相关文档同步
