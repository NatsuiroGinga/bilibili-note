# 知识库检索汇总：mcdn 探测

> 检索源：`~/Dev/Research`（Obsidian vault `Research`），使用 research-knowledge MCP（lexical 模式，命中 `bban-api` 项目域；跨库关联经核心文档深度 2 关联图谱发现）。
> 检索时间：2026-08-27

## 一、核心命中文档（bban-api 库）

| 文档 | 一句话内容 | Obsidian 跳转链接 |
|---|---|---|
| **mcdn-v-probe-task-system**（核心） | mcdn-v（视频云 MCDN）探测任务体系：候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建 → `percentage` 确定性抽样下发 → `generateNodeProbeTaskForResult` 结果查询严格分派；含 HTTP/ICMP/TCP 真实执行方（noded）核实与只读核查脚本 | `obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md` |
| **bban-probe-task-api** | 探测任务查询接口：查目标是否进入候选探测池应访问已签名 SLB 接口 `/api/bban2/v1/all-probe-task` 并精确匹配节点 ID，勿用 bvc-hub 代理 URL 重新签名 | `obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md` |
| **bban-mcdn-probe-targets** | mcdn 探测目标判定规则，与 SID 关联限制；关联探测接口、探测任务体系与设计来源 | `obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md` |
| **bban-taishan-probe-mapping** | 泰山 KV 存储分布（`bban_misc_kv` service_type / `bban_probe_kv` 探测结果）与 Taishan SCAN 查询方法 | `obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md` |
| **mcdn-probe-prometheus-exporter** | mcdn 探测结果 Prometheus exporter（监控指标暴露） | `obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` |
| **json-to-prometheus-textfile-workflow** | JSON 探测结果转 Prometheus textfile 格式的工作流 | `obsidian://open?vault=Research&file=bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` |

## 二、来源文档（Sources/Docs）

| 文档 | 说明 | Obsidian 跳转链接 |
|---|---|---|
| **et-bban-probe-design-docs** | mcdn 探测设计文档（`bban-mcdn-probe-targets` 与核心体系的来源） | `obsidian://open?vault=Research&file=bban-api/Sources/Docs/et-bban-probe-design-docs.md` |
| **bban-api-evidence** | bban-api 接口证据（`bban-probe-task-api` 的接口证据来源） | `obsidian://open?vault=Research&file=bban-api/Sources/Docs/bban-api-evidence.md` |
| moni-http-client-metric-cardinality / hawkeye-prometheus-openapi / hawkeye-prometheus-datasource-query | Moni / Hawkeye 监控查询接口与指标基数文档（与 exporter、监控链路关联） | `obsidian://open?vault=Research&file=bban-api/Sources/Docs/moni-http-client-metric-cardinality.md` 等 |

## 三、关联主题文档（入链/出链，同库）

- **bban-sid-lifecycle** — SID 生命周期（与 mcdn 探测目标判定、SID 关联限制相关）：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-sid-lifecycle.md`
- **bban-vod-reserve-gap** — 点播储备带宽差额（SID 业务规则，与探测目标判定互链）：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-vod-reserve-gap.md`
- **bban-node-field-semantics** — 节点字段语义（入链自核心文档）：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md`
- **bban-node-status-silent-success** — 节点状态静默成功（入链自核心文档）：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success.md`
- **bban-signature-body-coverage** — 签名 body 覆盖（与 `bban-probe-task-api` 的签名细节相关）：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-signature-body-coverage.md`

## 四、入口/索引/日志

- **00-Hub**（入口，最近更新记录 mcdn 探测进展）：`obsidian://open?vault=Research&file=bban-api/00-Hub.md`
- **02-Index**（索引）：`obsidian://open?vault=Research&file=bban-api/02-Index.md`
- **01-Plan**（计划）：`obsidian://open?vault=Research&file=bban-api/01-Plan.md`
- **Daily/2026-08-17**（日志，mcdn-v 探测任务验证过程）：`obsidian://open?vault=Research&file=bban-api/Daily/2026-08-17.md`

## 五、跨库关联（manba-bi 库，经核心文档关联图谱发现）

| 文档 | 主题推断 | Obsidian 跳转链接 |
|---|---|---|
| mcdn-cross-isp-packet-loss | MCDN 跨运营商丢包 | `obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-cross-isp-packet-loss.md` |
| mcdn-promql-monitoring | MCDN PromQL 监控 | `obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-promql-monitoring.md` |
| mcdn-vod-forbidden-scheduling | MCDN 点播禁调度 | `obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-forbidden-scheduling.md` |
| mcdn-vod-probe-config-rollout | MCDN 点播探测配置灰度 | `obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md` |
| Daily/2026-08-21 | manba-bi 日志（关联连接点） | `obsidian://open?vault=Research&file=manba-bi/Daily/2026-08-21.md` |

> 注：lexical 检索索引为 `bban-api` 项目域，manba-bi 文档无法直接命中，以上跨库文档及其 URI 来自核心文档 `mcdn-v-probe-task-system` 的 depth-2 关联图谱（BFS），主题为按文件名推断，内容未逐篇核实。

## 六、关联关系小结

- **主线**：`mcdn-v-probe-task-system`（任务体系）为枢纽，出链到 `bban-probe-task-api`（查询接口）、`bban-mcdn-probe-targets`（目标判定）、`mcdn-probe-prometheus-exporter` 与 `json-to-prometheus-textfile-workflow`（结果监控）、`et-bban-probe-design-docs`（设计来源）；入链自 `00-Hub`、`02-Index`、`01-Plan`、`_system/registry`、`Daily/2026-08-17`。
- **目标判定分支**：`bban-mcdn-probe-targets` ⇄ `bban-sid-lifecycle` ⇄ `bban-vod-reserve-gap`（SID 关联限制三角）。
- **接口证据分支**：`bban-probe-task-api` → `bban-api-evidence`（证据）、`bban-signature-body-coverage`（签名细节）。
- **监控/存储分支**：`mcdn-v-probe-task-system` → `bban-taishan-probe-mapping`（探测结果泰山存储）、`mcdn-probe-prometheus-exporter` + `json-to-prometheus-textfile-workflow`（Prometheus 监控链路），并延伸至 Moni/Hawkeye 监控来源文档。
- **跨库**：经关联图谱延伸至 `manba-bi` 的 MCDN 运维/监控/探测配置文档。
