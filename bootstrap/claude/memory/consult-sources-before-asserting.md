---
name: consult-sources-before-asserting
description: 不确定时主动查原件与文献，不要等用户提醒，也不要凭记忆断言
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4c263012-e9e8-4408-9faf-e935afd08d0b
  modified: 2026-08-17T11:23:12.386Z
---

遇到自己不知道或不确定的事，**先去查原件、查文献、查源码，再开口**。不要等用户提醒「去查一下」，也不要用「通常」「一般来说」「应该」把记忆包装成结论。

**Why:** 2026-08-17 一次会话里连续出现三类同型问题。其一，写作规范里没写「不许做统计」，导致 3.6 搬进了方差分析、F 统计量、p 值与置信区间；用户问「朱的论文有关于种子的论述吗」，我才去 `pdftotext` 检索，结果是全文 259,201 字符中种子与全部统计术语**零命中**。其二，用户问「朱的论文中有参数量的说明吗」，我才去查，结果朱在多处报参数量、显存与吞吐，并把参数规模作为选骨干的显式维度——**我本可以据此更早地把「以 1/119 参数量领先」写成加分论断**。其三，用户问「paper-miner 能不能用看看别人怎么写」，我才去挖，而本地早有 `2022-Lichy-RF-Beats-CNN-GRU-Encrypted-Malware.pdf` 这篇「简单模型打赢深度模型」的现成范本。三次都是用户先问、我后查，等于把检索成本转嫁给了用户。

同一模式在接口层也发生过两次：`torch.flatnonzero` 不存在导致实验失败，`swanlab` 的 `run.public` 凭记忆写错导致首个 run 崩溃；同一事故里我还反向断言 `experiment_name=` 无效，实测有效。**凭记忆断言接口「不存在」与断言其「存在」同样不可靠。**

**How to apply:** 触发词是「朱是怎么做的」「别人怎么写」「这个接口叫什么」「这个字段有没有」「这个做法常不常见」——出现任何一个，先查再答。本地 `raw/papers/` 有 427 篇 PDF，`pdftotext` 加 `rg` 几秒出结果；第三方接口走 `npx ctx7@latest library/docs`；仓库事实走 `rg` 与实际文件。查完在回答里给出检索式与命中数，让用户能复核。查不到就说查不到并列出已试入口，不要用推断填空。相关：[[align-to-published-papers-not-own-taxonomy]]、[[falsify-directions-with-experiments-not-speculation]]、[[download-and-note-every-cited-paper]]。
