# Research-Ideation 文献委派迁移报告

## 迁移结果

1. 新增 Codex 原生代理 `/Users/bilibili/.codex/agents/literature-reviewer.toml`，完整迁移范围定义、检索收集、筛选分类、全文分析、综合空白和生成制品六阶段流程。
2. 新增 `/Users/bilibili/.agents/skills/research-ideation/references/literature-reviewer-delegation.md`，规定触发条件、任务合同、显式委派模板、六阶段验收和降级路径。
3. 更新 `/Users/bilibili/.agents/skills/research-ideation/SKILL.md` 至 `0.2.0`，把文献证据阶段改为强制委派，并保留主代理对澄清、研究问题选择、证据门禁和最终综合的责任。
4. Zotero 改为条件能力：仅在已配置且可写时导入；不可用时保留项目证据链，不得声称已写入 Zotero。

## 行为对比

- 改造前：同一系统综述场景会由主代理自行规划七步流程，不会委派 `literature-reviewer`。
- 改造后：主代理先固定任务合同，再显式使用注册代理名 `literature-reviewer`；通用子代理运行时任务名为 `literature_reviewer`。全部六阶段通过后才允许进入研究空白、研究问题卡和提案门禁。

## 验证

- Prettier 已格式化技能正文与委派参考文档。
- Codex 迁移验证器确认 `literature-reviewer.toml` 具有全部必填字段，退出码为 `0`。
- 同一改造后行为场景复验通过；任务合同字段、代理名称、六阶段门禁与引用路径一致。
- 验证器报告的 `computer-use` 命令缺失和第三方 React `AGENTS.md` 体积警告为既有环境问题，与本次迁移无关。

## 使用方式

后续调用 `research-ideation` 且任务进入多论文检索、全文分析或证据性研究空白识别时，主代理必须读取委派协议并启动 `literature-reviewer`，不得自行替代六阶段文献综述。
