# Research-Ideation 文献委派改造笔记

## 已核实事实

- Claude 原代理位于 `/Users/bilibili/.claude/agents/literature-reviewer.md`，流程为范围定义、检索收集、筛选过滤、全文分析、综合发现和生成制品六阶段。
- 当前 `research-ideation` 位于 `/Users/bilibili/.agents/skills/research-ideation/SKILL.md`，包含内置文献综述与 Zotero 流程，但没有 `literature-reviewer`、`spawn_agent` 或强制委派指令。
- Codex 本机代理位于 `/Users/bilibili/.codex/agents/`，使用 TOML 字段 `name`、`description` 和 `developer_instructions`。
- 改造前行为检查确认：代理会自行规划七步综述，不会显式委派专门文献代理。
- 独立格式审计确认 `.claude/agents/*.md` 应迁移到 `.codex/agents/*.toml`；本机 `agent-identifier` 技能仍描述旧 Markdown 格式，不能作为当前 TOML 验证依据。
- Codex 迁移器提供目标验证入口，可检查代理 TOML 必填字段；运行时任务名使用 `literature_reviewer`，注册代理名保持 `literature-reviewer`。

## 迁移约束

- 技能正文保持简洁，六阶段细节放入专用代理与委派参考文档。
- 委派提示必须包含研究问题、时间范围、纳入排除条件、证据强度、输出路径和停止条件。
- 全文证据与摘要证据必须区分；无法核验的文献不能支撑强结论。
- 联网发现且判断有用的论文，应遵守当前项目 `AGENTS.md` 的下载与阅读笔记规则。
