# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

这是一个 **Obsidian 笔记仓库**（Vault），不是代码仓库。所有内容为 Markdown 格式的中文笔记，记录 Bilibili CDN 基础设施运维、论文阅读和知识管理方法论。

## 三层架构

仓库遵循 **raw / wiki / output** 三层模型：

```
note/
├── CLAUDE.md      # ← 本文件：AI 的员工手册
├── SCHEMA.md      # wiki 的"宪法"：笔记类型定义 + 模板规范
├── raw/           # 第一层：外部源材料（不可变，只增不改）
│   ├── papers/    # 论文 PDF 原件（8 篇）
│   └── README.md  # raw 层规则说明
├── wiki/          # 第二层：结构化知识（AI 维护，持续演化）
│   ├── INDEX.md   # 全局 MOC 索引
│   ├── go-op/     # Bilibili 运维平台后端
│   ├── te/        # 网络遥测服务 bili-tellurium
│   ├── papers/    # 论文的结构化阅读笔记
│   └── methodology/ # 工作流和设计原则
└── output/        # 第三层：查询产物（临时报告/分析，可覆盖）
```

**关键约束：**
- `raw/` 中的文件不可修改——只能新增。所有理解和分析写入 `wiki/`
- `wiki/` 是知识的主体，AI 从这里读取和写入结构化笔记
- `output/` 是临时工作区，不沉淀长期知识
- 创建新笔记前先查 `SCHEMA.md` 确认模板和必填字段

## wiki 层项目域

### go-op — 运维平台后端

Bilibili 运维平台 Go 微服务项目，包含四个服务：`manba-bi`（BI 分析/踢点处理）、`manba-computer`（计算服务）、`manba-dispatcher`（调度分发）、`portal`（运维门户核心）。统一架构：`cmd/main.go` → `internal/{dao, model, server, service}` → `configs/`。

- `wiki/go-op/项目架构与核心知识.md` — 域入口 MOC
- `wiki/go-op/cpu-top/` — MCDN 节点 CPU 高负载分析，6 台机器 + 总览。核心结论：回源带宽 → si↑ + bvc↑ → CPU busy > 80% → 下线
- `wiki/go-op/docs/` — 技术设计文档和排查总结
- `wiki/go-op/rules/mysql.md` — `msg_data_all` 表结构知识库

### te（bili-tellurium）— 网络遥测服务

从 Prometheus 采集指标，流水线模式（Collection → Data Cube → Intent Model → Action）做自动化决策。

- `wiki/te/项目架构与核心知识.md` — 域入口 MOC
- `wiki/te/specs/` — 设计文档（水位线检测、双通道配置巡检）
- `wiki/te/CHANGELOG.md` — 版本历史

### papers — 论文阅读

论文 PDF 原件存放于 `raw/papers/`，结构化理解笔记存放于 `wiki/papers/`。每篇论文笔记必须含 `source_pdf` 字段指向 raw 原件。

### methodology — 方法论

知识库工作原理和工作流优化原则。

## 笔记命名与组织约定

- **MOC 笔记**：`INDEX.md`（根 MOC）或 `项目架构与核心知识.md`（域 MOC）
- **设计文档**：`wiki/{项目}/docs/` 或 `wiki/{项目}/specs/`，文件名含日期 `YYYY-MM-DD-` 前缀或纯描述性标题
- **排查分析**：放在具体主题子目录（如 `wiki/go-op/cpu-top/`），单篇分析加总览索引 MOC
- **参考知识库**：`wiki/{项目}/rules/` 下存放供 AI 查阅的结构化知识
- **论文笔记**：`wiki/papers/{方向}/{标题}.md`，`source_pdf` 字段必填
- **文件命名**：中文优先，可混用日期前缀；避免文件名含 `&` 等特殊字符

## 笔记模板

创建新笔记前，先查 `SCHEMA.md` 确认对应类型的模板和必填字段。通用必填：
- `title` / `date` / `tags`（含 `类型/xxx` 标签）

论文笔记额外必填：`authors` / `year` / `journal` / `source_pdf` / `key_finding`

## 已知问题

1. `wiki/go-op/cpu-top/` 文件名含运营商/机房长标识，统一截取主机名段更清晰。
2. 仓库缺少 git 版本控制（2026-07-13 已初始化 `git init`）。
3. `raw/papers/` 中有 5 篇论文 PDF 待确认主题并建立 wiki 笔记。
