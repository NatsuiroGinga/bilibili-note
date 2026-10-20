# 知识库检索结果：mcdn 探测移植

检索方式：`research-knowledge` MCP，scope=`bban-api`（lexical + semantic 双模式）；关联发现用 `knowledge_related`（depth=1）。

> 提示：lexical 检索"mcdn 探测"命中率低且分散，semantic 模式（"mcdn 探测 移植 probe 迁移 任务" score 0.88+）准确命中核心文档。主题没有名为"移植/迁移"的独立条目，实质沉淀集中在 mcdn-v 探测任务体系下。

## 检索结果

- **mcdn-v-probe-task-system**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
  - 摘要：mcdn-v（视频云 MCDN）探测任务分三层：候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建，miner 实际任务由 `percentage` 确定性抽样产生（`sort.Strings(allIds)` 后取前 `ceil(len*percentage/100)`，非随机），结果查询用独立的 `generateNodeProbeTaskForResult` 严格分派——读路径不容错、写路径降级。已核实 HTTP/ICMP/TCP 探测的真实执行方为 noded 源码（`/Users/bilibili/Dev/bi`，仓库 `bvccdn-noded`），非"强推断"而是代码确证。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md)

- **bban-taishan-probe-mapping**（`bban-api/Knowledge/bban-taishan-probe-mapping.md`）
  - 摘要：泰山存储分布：`bban_misc_kv`（service_type）与 `bban_probe_kv`（探测结果），并给出 Taishan SCAN 查询方法。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md)

- **bban-probe-task-api**（`bban-api/Knowledge/bban-probe-task-api.md`）
  - 摘要：BBAN Probe Task API（探测任务接口，与 mcdn-v-probe-task-system 直接关联）。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md)

- **bban-mcdn-probe-targets**（`bban-api/Knowledge/bban-mcdn-probe-targets.md`）
  - 摘要：mcdn 探测目标判定与 SID 关联限制（mcdn 探测目标的判据边界）。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md)

## 关联文档

对核心文档 `mcdn-v-probe-task-system` 做 depth=1 关联发现：

- **出链（它引用谁）**：
  - `bban-api/Knowledge/bban-probe-task-api.md` ×1
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md` ×1
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md` ×1（探测设计文档，来源资料）
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` ×1
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` ×1

- **入链（谁引用它）**：
  - `bban-api/Knowledge/bban-taishan-probe-mapping.md` ×1
  - `bban-api/Knowledge/bban-node-status-silent-success.md` ×1
  - `bban-api/Knowledge/bban-node-field-semantics.md` ×1
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md` ×1
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` ×1
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` ×1
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md` ×1
  - 导航/索引类（降权）：`00-Hub.md`、`02-Index.md`、`01-Plan.md`、`_system/registry.md`、`Daily/2026-08-17.md`

- **对 `bban-taishan-probe-mapping` 的关联**：
  - 出链：`bban-api/Knowledge/mcdn-v-probe-task-system.md` ×1
  - 入链：`00-Hub.md`、`02-Index.md`、`_system/registry.md`

## 图谱提示

可在 Obsidian Graph View 查看可视化图谱：打开 `~/Dev/Research` vault，点左侧图谱图标；该库图谱 canvas 为 `bban-api/Maps/bban-api-knowledge.canvas`。mcdn 探测主题以 `mcdn-v-probe-task-system` 为中心节点，向外辐射探测 API、目标判定、泰山存储、Prometheus 导出四条关联边。

## 结论

知识库对"mcdn 探测移植"有成熟沉淀，核心是 `bban-api/Knowledge/mcdn-v-probe-task-system.md`（2026-08-17 起持续验证 mcdn-v 节点探测任务，2026-08-27 已确认端到端验证门槛），并配套设计文档、API、存储映射等关联条目。直接引用该 Knowledge 条目的结论即可，无需重新调研。若任务是"将旧系统（et/bbanv1）探测移植到 bban2"，建议结合 `et-bban-probe-design-docs.md`（设计文档）与 `bban-probe-task-api.md`（接口层）交叉核对。
