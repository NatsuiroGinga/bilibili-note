---
name: no-sleep-polling-use-background-tasks
description: 禁止用 sleep 死等实验结果，改用后台任务或立即只读检查
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 068bbd7d-1e28-42ae-9da2-046f106e4118
  modified: 2026-08-12T05:38:56.502Z
---

禁止在 Bash 里用 `sleep N` 死等远程或本地实验完成。要么用 `run_in_background: true` 让任务跑完自动通知，要么立即执行一次只读状态检查（`tail` 日志 + `screen -ls` + 进程/文件时间戳）后把控制权交回用户。

**Why:** 用户明确制止。`sleep` 占住整个工具调用回合、阻塞对话、既拿不到中间结果也无法响应新指令，而且一旦估错时长就白等——实验状态本来就可以随时只读查询。

**How to apply:** 长任务在服务器上用 `screen -dmS <name>` 启动，然后单次 `tail -N <log>` 查看进度并立即返回；需要等待完成时用 Bash 的 `run_in_background` 或 Agent/Workflow 的后台机制，由完成通知驱动下一步。相关：[[falsify-directions-with-experiments-not-speculation]]
