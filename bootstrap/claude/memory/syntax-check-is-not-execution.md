---
name: syntax-check-is-not-execution
description: bash -n 与 py_compile 只证明能解析，交付脚本前必须真实执行一次
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a3343a71-d8d8-4b02-8183-7a33d515e161
  modified: 2026-08-29T06:20:24.464Z
---

`bash -n` 通过、`py_compile` 通过、导入检查通过，都**不证明脚本能工作**。交付或提交任何
脚本前，必须用真实参数真实执行一次，并检查它的输出是否是预期的。

**Why:** 2026-08-29 提交的 `pull_ch3_ft_four_cell_artifacts.sh` 同时有三个致命缺陷，
`bash -n` 全部放行：用 `bash` 去运行 `#!/usr/bin/expect` 的 Tcl 脚本（一执行就语法错误）、
把 stderr 全部 `>/dev/null` 吞掉、退出码被管道掩盖。三重掩盖使一个**必然失败**的回传
在日志里显示为「远端尚无该项，跳过」，完全看不出故障。同一天 `expect -c 'script' a b`
的参数传递也是写完才发现不填充 argv。这些都不是粗心，是验证深度不够——
本仓库已有两起同型事故（`torch.flatnonzero` 不存在、`swanlab` 的 `run.public` 不存在），
共同点都是「语法通过」被当成「能工作」。

**How to apply:** 写完脚本先跑，再提交，顺序不能反。跑的时候：不要把 stderr 丢掉；
用管道时记得 `PIPESTATUS` 或直接不用管道，否则退出码是 `tail` 的不是脚本的；
输出里出现「跳过」「可能尚未产生」这类兜底分支时，主动确认它是真的该跳过，
而不是掩盖了错误。周期性脚本还要计时——单轮耗时超过调用方超时就等于没跑。
与 [[consult-sources-before-asserting]] 是同一族问题的两个面：
那条讲「别凭记忆断言接口」，这条讲「别凭静态检查断言能跑」。
