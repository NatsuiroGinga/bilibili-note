# 库文档查询：ctx7 CLI（精简版）

用户问到任何库/框架/SDK/API/CLI 工具/云服务的用法、配置、版本迁移、报错或 CLI 用法时，**必须**用 `npx ctx7@latest` 查当前官方文档，即使自认为已掌握——训练数据可能过期；优先于 web search。不适用于：重构、从零写脚本、调试业务逻辑、code review、通用编程概念。

流程（两步，同一问题 ≤3 条命令）：
1. `npx ctx7@latest library <官方库名含标点> "<具体查询>"` → 从 `/org/project` 中选最匹配的 ID（名称精确、文档量大、声誉高优先；用户给了版本号用 `/org/project/version`）
2. `npx ctx7@latest docs <libraryId> "<单一概念的specific查询>"` → 基于返回的文档回答

规则：除用户直接给出 ID 外必须先 library 后 docs；查询要具体、一条命令一个概念；查询不得包含密钥/凭据等敏感信息。报 quota 错误时告知用户并建议 `npx ctx7@latest login` 或设置 `CONTEXT7_API_KEY`，禁止静默回退到训练数据。
