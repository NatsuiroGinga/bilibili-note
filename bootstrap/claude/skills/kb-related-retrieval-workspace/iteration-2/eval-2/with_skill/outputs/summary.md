# 知识库 Taishan/泰山 存储资料检索结果

> 检索范围：`bban-api` 库（scope=bban-api）
> 检索方式：semantic + lexical 双模式（中文 semantic 命中质量最佳，score 0.87-0.88）

## 结论先行

**知识库中有专门的 Taishan/泰山 存储资料**。核心文档是 `bban-api/Knowledge/bban-taishan-probe-mapping.md`（2026-08-27 补充），覆盖 Taishan 存储分布、配置开关、KV 表格与查询方法；另有一篇高度关联的 `mcdn-v-probe-task-system.md` 在探测任务系统多处涉及 Taishan 读写与容错。两者构成 Taishan 存储主题的核心知识簇。

## 检索结果

- **Taishan 查询方法 / 存储分布与配置开关（`bban-api/Knowledge/bban-taishan-probe-mapping.md`）**
  - 摘要：service_type 与探测结果的读写源由配置开关 `serviceFromTaishan`/`qosFromTaishan` 决定（`app/admin/configs/application.toml`）。Taishan 表格为 `bban_misc_kv`（service_type，key `{bban2:portal_mcdn}$service_type`，string JSON）与 `bban_probe_kv`（探测结果，V2 key `{bban2_probe_result:<nodeID>}$<type>$<source>`）。Taishan 无原生 HGETALL，ba 用 **SCAN**（KeyPrefix=hashKey，单次 1000 条分页）封装 hgetall 语义（taishan.go:121-126）；Taishan 是 gRPC KV：`table` + `token` + `key`，无 redis-cli 式命令。查询探测结果用 SCAN `bban_probe_kv`，KeyPrefix `{bban2_probe_result:<nodeID>}`；查 service_type 用 GET `bban_misc_kv`。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md`

- **mcdn-v-probe-task-system.md（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）**
  - 摘要：mcdn-v 目标判定链、候选池抽样下发、结果查询分派均依赖 Taishan。**容错不对称（重要）**：结果查询对 Taishan 失败严格报错 `fmt.Errorf("...: %w", err)` 不降级，下发路径降级跳过（probe.go:88-90）；`QueryAllPortalServiceTypeFromTaishan` 的 Taishan 缓存键与刷新周期列在"待验证"。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md`

- 命中检索词的导航/索引文件（次要）：`bban-api/00-Hub.md`（最近更新、下一步）、`bban-api/02-Index.md`、`bban-api/_system/registry.md`

## 关联文档

- 出链（bban-taishan-probe-mapping.md 引用谁）：
  - `bban-api/Knowledge/mcdn-v-probe-task-system.md` ×1

- 入链（谁引用 bban-taishan-probe-mapping.md）：
  - `bban-api/00-Hub.md` ×1
  - `bban-api/02-Index.md` ×1
  - `bban-api/_system/registry.md` ×1

- 图扩展（depth=2，经 mcdn-v-probe-task-system 等 BFS 扩展出的相关 Knowledge/Sources 条目）：
  - `bban-api/Knowledge/bban-probe-task-api.md`（探测任务 API，任务下发/结果查询接口层）
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md`（mcdn 探测目标判定）
  - `bban-api/Knowledge/bban-node-field-semantics.md`（节点字段语义）
  - `bban-api/Knowledge/bban-node-status-silent-success.md`（节点状态静默成功）
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md`
  - `bban-api/Knowledge/bban-signature-body-coverage.md`
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md`（探测设计文档来源）
  - `bban-api/Sources/Docs/bban-api-evidence.md`（证据库）
  - `bban-api/Daily/2026-08-17.md`（当日验证记录）
  - `bban-api/01-Plan.md`（计划，入链）

## 主题内聚说明

Taishan 存储主题的**核心簇** = `bban-taishan-probe-mapping.md`（存储分布+查询方法）+ `mcdn-v-probe-task-system.md`（读写与容错语义）。向下游任务 API、目标判定、节点状态等条目扩散。导航文件（00-Hub / 02-Index / registry）仅做索引登记，降权处理。

## 图谱提示

可在 Obsidian Graph View 查看可视化图谱：打开 `~/Dev/Research` vault，点击左侧图谱图标，聚焦 `bban-api/Knowledge/bban-taishan-probe-mapping.md` 可看到以它为中心的关联网络。另有 bban-api 图谱 canvas：`bban-api/Maps/bban-api-knowledge.canvas`。

## 下一步建议

- 若需深入了解 Taishan 底层交互，可读仓库代码 `app/admin/internal/service/probe.go` 与 taishan 相关 client（`taishan.go:121-126` 为 SCAN 封装点）。
- 若需确认 `QueryAllPortalServiceTypeFromTaishan` 的缓存键与刷新周期，该结论尚未沉淀（见 mcdn-v-probe-task-system.md "待验证"）。
