---
name: annotate-model-effort-on-every-dispatch
description: 每次派发或恢复子代理都要给出「代理名 → 完整模型 ID → effort」映射，续跑也算派发通知
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a6b7721f-65a8-411a-9630-071c1601ca01
  modified: 2026-08-19T07:50:13.119Z
---

**任何一次子代理的派发、重启或续跑，都必须在同一条回复里给出「代理名 → 完整模型 ID → `effort`」映射。** 恢复中断的代理**也算一次派发通知**，不能因为「首次派发时说过了」而略过。

**Why:** 2026-08-19 第三章定稿自审会话，我首次派发自审工作流时给了复杂度分级表，但会话额度打满导致 7 个代理全灭；额度恢复后我用 `resumeFromRunId` 重启，回复里只写「7 个代理运行中」，映射一个字没提。同一轮还续跑了文献代理，**连它的模型和 effort 都没核过就宣布已恢复**。用户直接质问「我不是让你启动 agent 的时候把模型名称和 effort 都标注吗」。

根因是把仓库 `AGENTS.md` 那句「**创建时**的进度通知和最终任务报告必须同时明确记录完整模型名与 `effort`」按字面读成只管首次创建，而重启、续跑、`SendMessage` 唤醒都被排除在外。实际用户要的是**每次代理开始干活时都知道它是什么档位**，与它是不是第一次启动无关。

事后核实的两个事实（都要从制品读，不能凭记忆）：
- 工作流代理的档位读**脚本文件本身**（`workflows/scripts/*.js` 里的 `model:` 与 `effort:`），不要凭派发时的印象复述。
- `Agent` 工具派发的代理读 `subagents/agent-<id>.meta.json`，其中有 `agentType` 与 `model`；**`effort` 往往不在 meta 里**，此时它继承会话 effort，应如实标为「未记录」，**不要编一个值**。transcript 里的 `"model":"claude-opus-5"` 可交叉验证 meta 的别名。

**How to apply:** 触发条件是任何 `Agent`、`Workflow`、`SendMessage` 唤醒或 `resumeFromRunId` 重启。在宣布代理已启动的**同一条回复**里给出映射表；工作流有多个阶段时逐阶段列，包括动态生成的代理（如按发现数量 fan-out 的证伪代理）。档位值一律从脚本或 meta 实测，缺失项标「未记录」。相关：[[invoke-skills-not-guess-from-names]]、[[consult-sources-before-asserting]]、[[delegate-complex-problems-to-fable5]]。
