---
name: match-model-tier-to-difficulty-not-importance
description: "派子代理按任务难度分档，不要因为任务\"重要\"就默认最强模型"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bf71861-639f-455d-b431-5dbc10e3331a
  modified: 2026-09-01T07:06:14.018Z
---

派子代理时**按难度分档，不按重要性分档**。规格明确的实现任务用 sonnet，
哪怕它影响关键结果；只有需要设计判断、证伪、架构取舍的才用 opus 或 fable。

仓库 `AGENTS.md` 的表：盘点查询下载 → 最轻档；**单模块实现与常规数据处理 → 中档**；
多文件实现与复杂实验诊断 → opus；理论设计与复杂文献综合 → fable。

**Why**：2026-09-01 一天里我派的代理几乎全是 opus——PLE 分词器实现、M-E 接线、
探针、训练侧实现、论文入库。用户直接问「你为什么每个任务都派 opus，单纯实现代码
交给 sonnet 啊」。复盘发现错误模式是**把「重要」当成了「难」**：那些任务确实影响
四格可比性和正文主张，但规格已被裁决报告的接口清单写死，几乎没有判断空间。

**How to apply**：派发前先问「这个任务的规格是否已经写死？」——若接口、验收命令、
判读规则都已给定，就是执行不是设计，用中档。若需要自己找方案、判断取舍、
对抗性证伪，才升档。**标注了模型和 effort 不等于分对了档**——
[[annotate-model-effort-on-every-dispatch]] 管的是如实报告，这条管的是分配本身。
相关：[[delegate-complex-problems-to-fable5]]。
