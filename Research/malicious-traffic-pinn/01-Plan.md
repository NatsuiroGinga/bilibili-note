# 01-计划与执行看板

## 当前优先级

- P0：建立项目骨架与可读迁移入口
- P1：`wiki/papers` 首批并行迁移到 `Sources/Papers/`
- P2：补齐主控文档与索引

## 当前任务

1. 创建 `Research/malicious-traffic-pinn` 项目骨架
2. 建立 `_system/registry.md` 初始结构
3. 确认与后续 `01-Plan.md` 同步的迁移策略

## 实验队列

- 先从 `wiki/papers` 中抽取首批 20~50 篇
- 继续验证 Zotero/来源文件关联

## 写作队列

- 待定：迁移完成后的结构说明与操作手册

## Current Research State

Current question: 如何在不破坏现有引用链的前提下完成渐进式迁移？
Current hypothesis: 分批创建新路径并保留旧路径可最小化风险。
Strongest evidence: 已完成 `obsidian-project-kb-core` 骨架规则梳理与执行路径定义。
Weakest evidence: 现有文件间存在版本命名差异与重复率，需逐批去重。
Open blockers: 某些笔记可能缺乏完整 frontmatter。
Next experiment: 先执行首批迁移并生成 registry 记录。
Do not repeat: 不在未验证前重命名原文件。
Last decision: 采用并行波次迁移（非一次性全量替换）。
