---
title: raw 层说明
date: 2026-07-14
tags:
  - 类型/参考
  - raw
---

# raw 层 — 源材料

## 规则

**只增不改。** raw/ 下的所有文件是知识的源头——PDF 原文、原始数据、外部导出文件。它们的价值在于**保持原貌**，不能被后续编辑覆盖。

- ✅ 新增源材料（放入 PDF / 文件）
- ❌ 修改已有源材料的内容
- ✅ 可以重命名使文件名更清晰
- ❌ 删除（除非确认是误入的无关文件）

## 当前内容清单

### raw/papers/ — 论文和文档原文

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `2512.24880v2.pdf` | mHC: Manifold-Constrained Hyper-Connections (DeepSeek) | [[mHC]] | ✅ 已有 |
| `Obsidian-AI-v1.0.0.pdf` | Obsidian-AI 知识库设计原则 | [[AI 知识库设计原则]] | ✅ 已有 |
| `北斗资源上下线&踢点逻辑.pdf` | 北斗踢点逻辑原始文档 | [[北斗资源上下线及踢点策略技术文档]] | ✅ 已有 |
| `2401.15839v1.pdf` | 待确认 | — | ⏳ 待读 |
| `atc24-zhang-rui-xiao.pdf` | 待确认 (USENIX ATC'24) | — | ⏳ 待读 |
| `nsdi22-paper-zhou.pdf` | 待确认 (NSDI'22) | — | ⏳ 待读 |
| `Proactive_Video_Push_CDN-P2P_VoD.pdf` | CDN-P2P 主动视频推送 | — | ⏳ 待读 |
| `视频CDN技术.pdf` | 视频 CDN 技术总览 (Bilibili) | — | ⏳ 待读 |

## 与 wiki 层的关系

`raw/` 的每个 PDF 应该在 `wiki/` 中有一篇对应的结构化笔记（`类型/论文`）。
wiki 笔记通过 `source_pdf` 字段指向 raw 原件，建立显式关联。
