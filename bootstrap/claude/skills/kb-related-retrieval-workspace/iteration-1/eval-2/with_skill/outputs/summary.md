# 知识库检索：Taishan / 泰山 存储

检索方式：research-knowledge MCP `knowledge_search(mode="lexical")` 多次查询（"Taishan 泰山 存储"/"泰山 KV 分布式存储"/"taishan"/"泰山"）均返回空（scope=common，未识别项目），按 skill 降级路径改用文件系统检索确认——知识库 **存在** Taishan/泰山 资料，核心沉淀在 `bban-api/` 库。MCP 索引与文件系统不一致，建议检查索引 scope 配置。

## 检索结果

- **泰山 service_type 映射在 mcdn-v 探测中的使用**（`~/Dev/Research/bban-api/Knowledge/bban-taishan-probe-mapping.md`，registry: knowledge-009）
  - 摘要：BA 通过泰山的 `SID → service_type` 映射识别 mcdn-v。存储分布：service_type 存 `bban_misc_kv`（key `{bban2:portal_mcdn}$service_type`），探测结果存 `bban_probe_kv`（V2 key `{bban2_probe_result:<nodeID>}$<type>$<source>`），由 `serviceFromTaishan`/`qosFromTaishan` 配置开关决定 Taishan/Redis 读写源。Taishan 是 gRPC KV（`table`+`token`+`key`），无原生 HGETALL，ba 用 SCAN（KeyPrefix=hashKey，单次 1000 条分页）实现 hgetall 语义。
  - 跳转：[obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fbban-taishan-probe-mapping](obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fbban-taishan-probe-mapping)

- **mcdn-v 探测任务体系**（`~/Dev/Research/bban-api/Knowledge/mcdn-v-probe-task-system.md`，registry: knowledge-003）
  - 摘要：mcdn-v 探测任务三层体系。Taishan 相关核心：SID→service_type 映射来自 `QueryAllPortalServiceTypeFromTaishan`（北斗同步写入）；**容错不对称**——下发路径对 Taishan 查询失败降级跳过 mcdn，结果查询路径严格报错不降级；admin 侧存储链路 `admin → Redis / Taishan`。
  - 跳转：[obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fmcdn-v-probe-task-system](obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fmcdn-v-probe-task-system)

- **MCDN 探测结果转 Prometheus：三套独立体系与 mcdn_probe.py**（`~/Dev/Research/bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`，registry: knowledge-006）
  - 摘要：区分三套"MCDN 质量"体系。体系 A（探测任务结果）存储 Redis/Taishan（按 `TargetNodeID` 索引）；体系 B（拨测 dialing）用**独立 Taishan 表**（按 `isp_province` 索引，`taishan_dialing.go` 的 `QueryDialingTaskResult`，Go 服务内建 promauto 读 Taishan 产出 `bban2_dialing_*` 指标）。
  - 跳转：[obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fmcdn-probe-prometheus-exporter](obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fmcdn-probe-prometheus-exporter)

- **把任意 REST JSON 接口转成 Prometheus 指标的通用工作流**（`~/Dev/Research/bban-api/Knowledge/json-to-prometheus-textfile-workflow.md`，registry: knowledge-007）
  - 摘要：从 exporter 案例提炼的通用清单；提及 `prom_metrics.go` 的 `updateDialingResultMetrics` 定时读 Taishan 写 GaugeVec 作为"服务内建指标"路线示例。
  - 跳转：[obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fjson-to-prometheus-textfile-workflow](obsidian://open?vault=Research&file=bban-api%2FKnowledge%2Fjson-to-prometheus-textfile-workflow)

## 关联文档

- **出链（核心条目引用谁）**
  - `bban-taishan-probe-mapping` → `Knowledge/mcdn-v-probe-task-system` ×1
  - `mcdn-v-probe-task-system` → `Knowledge/bban-probe-task-api`、`Knowledge/bban-mcdn-probe-targets`、`Knowledge/mcdn-probe-prometheus-exporter`、`Knowledge/json-to-prometheus-textfile-workflow`、`Sources/Docs/et-bban-probe-design-docs` ×5
  - `mcdn-probe-prometheus-exporter` → `Knowledge/mcdn-cross-isp-packet-loss`、`Knowledge/mcdn-promql-monitoring`（体系 C 相关）

- **入链（谁引用核心条目）**
  - `bban-taishan-probe-mapping` ← `bban-api/00-Hub.md`、`bban-api/02-Index.md`、`bban-api/_system/registry.md`（导航/索引，×3）
  - `mcdn-v-probe-task-system` ← `Knowledge/bban-node-field-semantics`、`Knowledge/bban-node-status-silent-success`、`Knowledge/bban-mcdn-probe-targets`、`Sources/Docs/et-bban-probe-design-docs`（实义引用）+ `00-Hub.md`、`02-Index.md`、`01-Plan.md`、`Daily/2026-08-17.md`、`_system/registry.md`（导航/待验证项）

- **待入库草稿（未计入索引，`retrieval: false`）**
  - `_ingestion-staging/20260827T161550+0800-mcdn-v-probe-port/drafts/probe-data-storage-and-taishan.md`——《探测数据存储分布与 Taishan 查询方法》（内容与 bban-taishan-probe-mapping 高度重合，promotion: pending，建议合并入 Knowledge）
  - `_ingestion-staging/20260820T195455+0800-all-dev-docs/drafts/bban-api-taishan-probe-mapping.md`（早期草稿）

## 图谱提示

可在 Obsidian Graph View 查看可视化图谱：打开 `~/Dev/Research` vault，点左侧图谱图标；bban-api 库另有画布 `bban-api/Maps/bban-api-knowledge.canvas`。

## 关键结论

1. **有泰山专属知识条目**：`bban-taishan-probe-mapping`（knowledge-009）是最直接命中，覆盖存储分布、配置开关、SCAN 查询方法。
2. **Taishan 是贯穿 mcdn-v 探测主线的存储层**：service_type 与探测结果读写、dialing 拨测结果，均涉及泰山/Redis 双源切换（配置开关控制）。
3. **检索链路提示**：MCP lexical 检索对 "taishan/泰山" 零命中而文件系统有大量真实内容，索引 scope（common）与文件不一致，后续应修复索引或使用 `knowledge_reindex` 后重试。
