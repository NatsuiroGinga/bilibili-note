# 知识库检索结果：mcdn 探测

- 检索方式：research-knowledge MCP，scope=`bban-api`，mode=`semantic`（中文查询）
- 检索词："mcdn 探测 泰山 存储 节点状态" / "mcdn 探测" / "探测任务接口 路径映射 直连鉴权 返回语义"
- 关联发现：`knowledge_related(depth=1)` 出链+入链

## 检索结果

### 核心 Knowledge 文档（沉淀价值最高）

- **mcdn-v-probe-task-system**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
  - 摘要：mcdn-v 探测任务体系。候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建，miner 任务由 `percentage` 确定性抽样产生（sort+ceil，非随机）；结果查询用独立 `generateNodeProbeTaskForResult` 严格分派——读路径不容错、写路径降级。已用 noded 源码确证 HTTP/ICMP/TCP 真实执行方。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md

- **bban-mcdn-probe-targets**（`bban-api/Knowledge/bban-mcdn-probe-targets.md`）
  - 摘要：mcdn 是否可被下发探测，先看北斗同步的业务类型（SID → `service_type`，点播用 `v`），再看人工探测配置和目标 IP；不要根据主机名或节点 ID 字面形式自行判断。候选池不以在线/离线状态作额外判定。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md

- **bban-probe-task-api**（`bban-api/Knowledge/bban-probe-task-api.md`）
  - 摘要：探测任务接口的路径映射、直连鉴权与返回语义（与上述两文档互相引用）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md

- **bban-taishan-probe-mapping**（`bban-api/Knowledge/bban-taishan-probe-mapping.md`）
  - 摘要：泰山存储分布与配置开关。`serviceFromTaishan`/`qosFromTaishan`=true 时 service_type 存 `bban_misc_kv`（key `{bban2:portal_mcdn}$service_type`）、探测结果存 `bban_probe_kv`（V2 key `{bban2_probe_result:<nodeID>}$<type>$<source>`）；=false 时回退 Redis。含 Taishan SCAN 查询方法。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md

- **mcdn-probe-prometheus-exporter**（`bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`）
  - 摘要：把本条目探测结果转成 Prometheus 指标（探测结果监控导出）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter.md

- **json-to-prometheus-textfile-workflow**（`bban-api/Knowledge/json-to-prometheus-textfile-workflow.md`）
  - 摘要：JSON → Prometheus textfile 格式转换工作流（探测结果指标化配套）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/json-to-prometheus-textfile-workflow.md

### 来源文档（Sources/Docs）

- **et-bban-probe-design-docs**（`bban-api/Sources/Docs/et-bban-probe-design-docs.md`）：BBAN 探测设计文档，为上述 Knowledge 条目的来源。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Sources/Docs/et-bban-probe-design-docs.md
- **bban-api-evidence**（`bban-api/Sources/Docs/bban-api-evidence.md`）：证据记录。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Sources/Docs/bban-api-evidence.md

## 关联文档

### mcdn-v-probe-task-system.md（核心枢纽，关联最密）
- 出链（它引用谁）：bban-probe-task-api ×1、bban-mcdn-probe-targets ×1、et-bban-probe-design-docs ×1、mcdn-probe-prometheus-exporter ×1、json-to-prometheus-textfile-workflow ×1
- 入链（谁引用它）：00-Hub、02-Index、01-Plan、_system/registry、Daily/2026-08-17、bban-node-status-silent-success、mcdn-probe-prometheus-exporter、bban-node-field-semantics、bban-mcdn-probe-targets、json-to-prometheus-textfile-workflow、bban-taishan-probe-mapping、et-bban-probe-design-docs

### bban-mcdn-probe-targets.md
- 出链：bban-probe-task-api、mcdn-v-probe-task-system、et-bban-probe-design-docs
- 入链：00-Hub、02-Index、_system/registry、bban-vod-reserve-gap、bban-sid-lifecycle、mcdn-v-probe-task-system、et-bban-probe-design-docs

### bban-taishan-probe-mapping.md
- 出链：mcdn-v-probe-task-system
- 入链：00-Hub、02-Index、_system/registry

### 次级关联（入链涉及的其它 Knowledge 条目）
- **bban-node-status-silent-success**（`bban-api/Knowledge/bban-node-status-silent-success.md`）：节点状态"静默成功"语义（结果查询相关）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success.md
- **bban-node-field-semantics**（`bban-api/Knowledge/bban-node-field-semantics.md`）：节点字段语义。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md
- **bban-vod-reserve-gap**（`bban-api/Knowledge/bban-vod-reserve-gap.md`）：点播预留缺口（引用探测目标判定）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-vod-reserve-gap.md
- **bban-sid-lifecycle**（`bban-api/Knowledge/bban-sid-lifecycle.md`）：SID 生命周期（引用探测目标判定）。
  - 跳转：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-sid-lifecycle.md

### 导航 / 索引文件（降权）
- `bban-api/00-Hub.md`（当前焦点与最近更新都指向探测相关条目）：obsidian://open?vault=Research&file=bban-api/00-Hub.md
- `bban-api/02-Index.md`、`bban-api/01-Plan.md`、`bban-api/_system/registry.md`、`bban-api/Daily/2026-08-17.md`

## 图谱提示

可在 Obsidian Graph View 中打开 `~/Dev/Research` vault（点左侧图谱图标）查看可视化图谱。核心枢纽是 `Knowledge/mcdn-v-probe-task-system.md`，它以 `Knowledge/mcdn-v-probe-task-system` 为中心连接探测接口（bban-probe-task-api）、目标判定（bban-mcdn-probe-targets）、存储（bban-taishan-probe-mapping）与指标化（mcdn-probe-prometheus-exporter / json-to-prometheus-textfile-workflow），并上溯设计文档（et-bban-probe-design-docs）。项目级图谱 canvas：`bban-api/Maps/bban-api-knowledge.canvas`。
