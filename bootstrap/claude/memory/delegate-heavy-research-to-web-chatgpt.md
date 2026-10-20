---
name: delegate-heavy-research-to-web-chatgpt
description: 复杂思考/调研分析/文献搜索任务经 chatgpt-handoff 交网页版 ChatGPT，本地只做核验与裁决
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dd21cfbb-2258-4c7f-8426-9174ac5f836a
  modified: 2026-09-09T09:46:11.309Z
---

2026-09-09 用户裁决：遇到需要复杂思考、调研分析、文献搜索的问题，都通过 chatgpt-handoff 工具交出给网页版 ChatGPT（节省 Claude 额度与上下文），不再由本地会话直接承担这类宽泛重活。

**Why:** 用户已把 Codex 的 chatgpt-handoff 工作流（有界只读出站包 + 机械敏感预检 + 回收 inbox 标"外部候选"）迁移为 Claude Code 的 user 级 MCP `chatgpt-handoff-readonly`；网页输出始终只是未核验候选。

**How to apply:** 文献综述、机制反例、理论近邻排重、图表/笔记草稿类任务 → 按 `~/.claude/skills/chatgpt-handoff/SKILL.md` 走 init/create/发送/回收流程；权威核验、实验有效性裁决、冻结合同、代码、Git、服务器、凭据处理一律留在本地。与 [[delegate-complex-problems-to-fable5]] 的分工：本地子代理仍负责工程实现与对抗审查，跨应用的宽思慢想优先出给 ChatGPT。
