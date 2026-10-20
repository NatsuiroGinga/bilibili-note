# 知识库检索汇总：Taishan/泰山 存储

检索工具：research-knowledge MCP（lexical FTS5 模式，scope 自动落在 `bban-api` 项目库，索引 40 个文件）

## 核心文档

**`bban-api/Knowledge/bban-taishan-probe-mapping.md`** —「Taishan 探测结果映射」（唯一以 Taishan 为主题的知识文档，2026-08-27 补充）
[Obsidian 跳转](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md)

主要内容：
1. **存储分布与配置开关**：service_type 与探测结果的读写源由 `app/admin/configs/application.toml` 的 `serviceFromTaishan` / `qosFromTaishan` 开关决定：
   - `=true`（Taishan）：service_type 存 `bban_misc_kv`，key `{bban2:portal_mcdn}$service_type`（string JSON）；探测结果存 `bban_probe_kv`，V2 key `{bban2_probe_result:<nodeID>}$<type>$<source>`
   - `=false`（Redis）：key 为 `portal_mcdn_server_type_key`；探测结果用非 V2 key（HSET，双写）
   - 探测配置存 MySQL `bban_probe_config`（`node_id` + `dtime=0`），节点存 `bban_node`
2. **Taishan 查询方法**：Taishan 无原生 HGETALL，ba 用 **SCAN**（`KeyPrefix`=hashKey，单次 1000 条分页）封装实现 hgetall 语义（taishan.go:121-126）；Taishan 是 gRPC KV（`table` + `token` + `key`），无 redis-cli 式命令。查探测结果 SCAN `bban_probe_kv`，查 service_type GET `bban_misc_kv`。

## 直接引用 Taishan 的关联文档

**`bban-api/Knowledge/mcdn-v-probe-task-system.md`** — mcdn-v 拨测任务系统
- 「候选池构建与抽样下发」：下发路径对 Taishan service 类型取值
- 「结果查询分派（容错不对称）」：结果查询对 Taishan 失败**严格**处理（容错不对称）
- 「mcdn-v 目标判定链」：依赖 Taishan（`taishan_...`）
- 「待验证」：涉及 Taishan 的查询方法待验证
- [Obsidian 跳转](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md)

## 入口/索引类（登记与引用）

- **`bban-api/00-Hub.md`** — 最近更新条目（2026-08-27）记载「补充泰山存储分布（`bban_misc_kv` service_type / `bban_probe_kv` 探测结果）与 Taishan SCAN 查询方法」；「下一步」提到「`result` 和 Taishan 写入」
  [跳转](obsidian://open?vault=Research&file=bban-api/00-Hub.md)
- **`bban-api/02-Index.md`** — 索引包含 `bban-taishan-probe-mapping` [跳转](obsidian://open?vault=Research&file=bban-api/02-Index.md)
- **`bban-api/_system/registry.md`** — 登记表（Knowledge 条目）[跳转](obsidian://open?vault=Research&file=bban-api/_system/registry.md)

## 关联图扩展（depth=2，间接相关）

来自 `bban-taishan-probe-mapping` 的关联图（均为 bban-api 项目库）：

- **Knowledge 层**：`bban-probe-task-api.md`（拨测任务 API）、`bban-mcdn-probe-targets.md`（mcdn 探测目标）、`bban-node-field-semantics.md`（节点字段语义）、`bban-node-status-silent-success.md`（节点状态静默成功）、`bban-signature-body-coverage.md`（签名 body 覆盖）、`json-to-prometheus-textfile-workflow.md`、`mcdn-probe-prometheus-exporter.md`
- **Sources/Docs 层**：`bban-api-evidence.md`、`et-bban-probe-design-docs.md`（拨测设计文档）、`moni-http-client-metric-cardinality.md`、`hawkeye-prometheus-openapi.md`、`hawkeye-prometheus-datasource-query.md`
- **其他**：`01-Plan.md`、`Daily/2026-08-17.md`

## 结论

- 知识库中 **Taishan/泰山 存储的直接资料集中在 1 篇**：`bban-taishan-probe-mapping.md`，主题是探测结果/service_type 在 Taishan 与 Redis 间的存储分布和 SCAN 查询方法。
- 关联最紧密的是 `mcdn-v-probe-task-system.md`（多个章节直接讨论 Taishan 读写与容错）。
- 其他文档（Hub/Index/registry 及拨测任务链）为登记、索引与同领域间接关联，不直接以 Taishan 存储为主题。
- 检索仅命中 `bban-api` 项目库（40 文件）；`manba-bi` / `te` 库无 Taishan 命中。
