---
name: delegate-complex-problems-to-fable5
description: 复杂任务派子代理时显式指定 model；但 fable 已改为画图专用，最强通用档是 opus
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dd21cfbb-2258-4c7f-8426-9174ac5f836a
  modified: 2026-10-13T09:47:57.569Z
---

派发 Agent 时要**显式指定 `model`**，不要留空（留空会继承会话模型，而会话模型往往不是最强档）。

**模型档位的当前实际映射（2026-10-13 用户纠正）**：

- **`opus` —— 最强通用推理档**。架构设计、数学形式化、对抗校验、路线裁决一律用它。
- **`fable` —— 已改为画图专用**，不再用于通用推理。
- `sonnet` —— 机械实现、常规工程。
- `haiku` —— 轻量任务。

**Why**：2026-10-13 我派数学攻坚时先用了默认档（继承会话模型）、又改用 `fable`，都被用户纠正。改用 `fable` 的那次直接失败：API 报 `reasoning_effort` 参数非法，且错误信息显示请求被路由到 `glm-5.3`（完全不同的模型）。**`fable` 不是通用推理档。**

**How to apply**：

1. 派 Agent 时**总是显式写 `model`**。
2. 数学／架构／对抗校验 ⇒ `opus`；机械实现 ⇒ `sonnet`；画图 ⇒ `fable`。
3. 记录档位时**如实写实际模型名**，不要把提示词里的强度措辞当成已生效配置（Agent 工具不暴露逐次 effort 参数）。
4. 派发后若失败，先看错误里的「model sent to the API」字段——它会暴露实际路由到了哪个模型。
