---
name: record-fixed-bugs-into-rules
description: 每修复一个缺陷都要写回故障防复发手册，并确保规则的路由触发词和可执行断言都到位
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 97fcf081-dc36-4726-bed9-74fa12edc4ee
  modified: 2026-08-07T07:10:42.346Z
---

用户要求：每次修复 bug 后，都把根因与检查写入 `.Codex/docs/agents-split/llm-probe-failure-prevention-handbook.md`，防止下次再犯。

**Why:** 2026-08-07 的 `rg --files` 忽略规则缺陷第二次复发，证明"写过散文规则"不等于"不会再犯"。复发有两个结构性原因：规则被挂在 `## SwanLab` 子节下，而 `thesis/experiments/llm_probe/AGENTS.md` 的路由触发词里没有"制品枚举"，所以只有在排查 SwanLab 故障时才会被读到；且规则没有任何可执行约束，新包装器漏掉时不会失败。

**How to apply:** 写回时做三件事，缺一不可——(1) 把规则放在与"违规发生时刻"匹配的章节，而不是"发现缺陷时刻"的章节；(2) 在对应 `AGENTS.md` 的按需路由触发词里加上该场景的关键词；(3) 在目标测试里加一条断言把规则变成可执行门禁。同时用 `rg` 扫描全仓同类调用点，把残留潜伏点列进手册，不要只改报错的那一行。相关：[[keep-handoff-doc-in-sync]]
