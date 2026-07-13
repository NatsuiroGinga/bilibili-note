# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

这是一个 **Obsidian 笔记仓库**（Vault），不是代码仓库。所有内容均为 Markdown 格式的中文笔记，记录 Bilibili CDN 基础设施运维相关的项目知识、排查分析和技术设计。

## 项目域

仓库按项目划分为三个顶层目录，各自独立但有业务关联：

### go-op — 运维平台后端

Bilibili 运维平台 Go 微服务项目，包含四个服务：`manba-bi`（BI 分析/踢点处理）、`manba-computer`（计算服务）、`manba-dispatcher`（调度分发）、`portal`（运维门户核心）。统一架构：`cmd/main.go` → `internal/{dao, model, server, service}` → `configs/`。

- `项目架构与核心知识.md` — 域入口索引，覆盖配置管理、MCDN 踢点体系、线路可用率、丢包率监控、通知体系、常用命令
- `rules/mysql.md` — `msg_data_all` 表结构、索引、性能问题与修复方案（嵌入的知识库，供 AI 参考）
- `cpu-top/` — MCDN 节点 CPU 高负载分析，6 台机器逐一分析 + 总览。核心结论：回源带宽 → si↑ + bvc↑ → CPU busy > 80% → 下线。`checkstatus-design.md` 是后续改造方案
- `docs/` — 技术设计文档和排查总结，按主题存放

### te（bili-tellurium）— 网络遥测服务

从 Prometheus 采集指标，流水线模式处理（Collection → Data Cube → Intent Model → Action），做自动化决策（节点/路径下架、水位线告警）。

- `项目架构与核心知识.md` — 域入口索引，覆盖架构、构建、测试、开发任务
- `CHANGELOG.md` — 版本历史
- `specs/` — 设计文档（水位线检测、双通道配置巡检）

### 项目间关系

go-op 是运维门户和调度平台，te 是网络遥测决策引擎。go-op 的 manba-bi 消费 te 产出的告警/数据，执行实际的节点上下线操作。两者共享 MCDN CDN 基础设施的业务上下文。

## 笔记命名与组织约定

- **域入口笔记**：`{项目}/项目架构与核心知识.md`，作为该域内容地图（MOC）
- **设计文档**：`{项目}/docs/` 或 `{项目}/specs/`，文件名含日期 `YYYY-MM-DD-` 前缀或纯描述性标题
- **排查分析**：放在具体主题子目录（如 `cpu-top/`），单篇分析加总览索引
- **参考知识库**：`{项目}/rules/` 下存放供 AI 查阅的结构化知识（如 MySQL 表结构）
- **文件命名**：全中文或日期-英文-中文混合，应避免文件名含 `&` 等特殊字符
- **内部链接**：Obsidian `[[双向链接]]` 使用较少，当前以独立文档为主

## 已知问题

1. `go-op/cpu-top/` 文件名含运营商/机房长标识，统一截取主机名段更清晰。
2. 仓库非 git 管理，无版本控制。
