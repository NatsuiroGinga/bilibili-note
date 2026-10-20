---
name: log-every-misjudgment
description: 每次做出被后续证据推翻的判断，必须落盘登记，不能只在对话里更正
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 14d4c97f-40f2-404b-a4ca-455e5e96bdb6
  modified: 2026-09-03T06:42:31.905Z
---

用户 2026-09-03 要求：**每当我做出误判，都要记录下来**，写进恢复卡的误判登记节或
`AGENTS.md`，也可以做成 hook。

**Why**：对话里的更正随会话消失，下一个会话会原样重犯。2026-09-03 一天内同型误判反复出现——
`flash-extract` 用错三次（用户已配 token 该用 `extract`）、把制品目录当协议推出「三口径三模型」、
「残差 425 秒不知去向」被 T3 实测推翻（实为模型计算占 93%）、把「FT-Transformer 线无调度器」
说成整个仓库无调度器。每一条在当时都口头更正了，但没有一条落盘。

**How to apply**：
- 判断被推翻的当轮就登记，不等任务结束——格式为「我当时断言什么／实测或文献是什么／
  错在哪一步推理／怎么避免」。**「错在哪一步」是重点**，只记结论无法防止复犯。
- 落点：`.Codex/docs/RWKV/RWKV第三章恢复卡.md` 的误判登记节；跨路线的通用教训写 `AGENTS.md`。
- 能机械检测的（命令用错、路径用错）**优先做成 hook 注入提示**，见 [[make-it-mechanical-not-remembered]]——
  文档只解决「查得到」，不解决「记得查」。
- 恢复卡有 500 行上限，误判登记只留一句摘要＋链接，详情进归档。

区别于 [[record-fixed-bugs-into-rules.md]]：那条管**代码 bug 修好后写回规则**，
这条管**我的推理错误**——包括没有代码 bug、纯属推断错的情况。
