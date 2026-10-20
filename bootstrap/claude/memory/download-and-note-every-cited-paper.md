---
name: download-and-note-every-cited-paper
description: 汇报中提到的每篇论文都必须下载全文并写 wiki 阅读笔记，只给题名或链接算任务未完成
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 665f7969-0e26-47cf-bc06-d42b90d8726a
  modified: 2026-08-08T03:36:26.138Z
---

凡是检索到并在回复中提及题名的论文，一律下载全文入 `raw/papers/` 并在 `wiki/papers/` 写结构化阅读笔记，同时更新方向 `INDEX.md`。只在对话里列出题名、链接或摘要，不算完成。

**Why:** 用户多次发现我在调研汇报里罗列了十几篇论文却一篇没落盘，导致证据链断裂——下次会话拿不到全文，结论无法复核，等于白调研。付费墙论文用户愿意手动下载，但前提是我把阻塞清单给全。

**How to apply:** 检索类任务结束前自查两遍——汇报里每个论文题名，(1) `raw/papers/` 有原件或进了阻塞清单？(2) `wiki/papers/` 有笔记？任一缺失即任务未完成。派发检索子代理时把这条写进提示。规则已落在 [[../../../personal/note/raw/AGENTS.md]]（原始材料规则「论文检索与落盘」节）。相关：[[record-fixed-bugs-into-rules]]
