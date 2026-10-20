# bban-api 知识库：node 状态相关文档与关联主题检索汇总

检索方式：research-knowledge MCP（`knowledge_search`，lexical 模式）检索 `~/Dev/Research` 知识库的 bban-api 项目库。

## 一、核心命中：node 状态相关文档（3 篇）

node 状态在 bban-api 知识库中并非单一主题，而是分散在 **接口静默行为、字段语义、探测任务门槛** 三个文档中，三者互为 wikilink 关联。

### 1. bban-node-status-silent-success（节点状态接口静默成功）
- 路径：`bban-api/Knowledge/bban-node-status-silent-success.md`
- Obsidian：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success.md
- 要点：`POST /v1/bban/node-status` 提交不存在的 node_id 会静默返回 `{"code":0,"message":"0","ttl":1,"data":"success"}`，返回 success 不等于状态已变更。两层危害：假成功（id 与 hostname 是不同字段，误用会"一台都没改"）+ 绕过熔断（未知 id 落入 others 分支，不参与 McdnFuseCheck 计数）。调用方必须回读 BBAN schedule 按 id 比对状态。

### 2. bban-node-field-semantics（节点可用性字段场景化语义）
- 路径：`bban-api/Knowledge/bban-node-field-semantics.md`
- Obsidian：obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md
- 要点：BBAN 里"节点能不能用"没有全局统一规则。`vod-play.can/status/frozen`、节点 `status/health`、`ipisps.forbidden` 在不同代码路径组合方式完全不同，按标签熔断容量计数、点播 MCDN 调度输出、逻辑交换机容量累计三个场景分别核验判定谓词（`CheckAbility` = Can && !Frozen；`AbilityAvailable` = Can && !Frozen && RtStatus；`HasAbility` 只看标签）。附五个字段业务含义与"配置拨测 ≠ 参与调度"注意事项。

### 3. mcdn-v-probe-task-system（mcdn-v 探测任务系统，含节点状态门槛）
- 路径：`bban-api/Knowledge/mcdn-v-probe-task-system.md`
- Obsidian：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md
- 要点：mcdn-v 探测任务系统中节点状态是任务生成门槛——`GenerateSimplifyTask` 在 prod 环境且 `!isNodeNormal(fromNode)` 时返回空任务；另有"节点状态非正常返回空任务"的环境判断与发布影响说明（pre/prod 发布差异）。

## 二、关联主题（wikilink 链接图谱）

核心文档所处的关联集群以 **探测任务（probe task）体系** 为主：

| 关联文档 | 类型 | 关系说明 |
| --- | --- | --- |
| `Knowledge/bban-probe-task-api` | Knowledge | 探测任务接口与鉴权（node-status 相关接口的上游） |
| `Knowledge/bban-mcdn-probe-targets` | Knowledge | mcdn 探测目标与候选池 |
| `Knowledge/mcdn-probe-prometheus-exporter` | Knowledge | 探测结果转 Prometheus 指标 |
| `Knowledge/json-to-prometheus-textfile-workflow` | Knowledge | 探测结果 JSON 转 Prometheus textfile 工作流 |
| `Knowledge/bban-taishan-probe-mapping` | Knowledge | Taishan 探测结果映射 |
| `Knowledge/bban-signature-body-coverage` | Knowledge | 请求签名 body 覆盖（鉴权相关） |
| `Sources/Docs/et-bban-probe-design-docs` | Sources | 探测设计文档（原始来源） |
| `Sources/Docs/bban-api-evidence` | Sources | bban-api 证据文档 |
| `Sources/Docs/moni-http-client-metric-cardinality` | Sources | 监控 HTTP 客户端指标基数 |
| `Sources/Docs/hawkeye-prometheus-openapi` / `hawkeye-prometheus-datasource-query` | Sources | 鹰眼 Prometheus 数据源查询 |
| `00-Hub` / `02-Index` / `01-Plan` / `_system/registry` / `Daily/2026-08-17` | 系统页 | 知识库枢纽、索引、注册表、日志 |

## 三、关联结构小结

- **直接节点状态文档**（3 篇）：接口静默行为 + 字段语义 + 探测任务节点门槛，三者两两互链。
- **外围关联**：均指向 mcdn-v 探测任务体系（接口、目标、指标导出、Taishan 映射、签名鉴权）。
- **语义侧重**：node 状态的工程语义集中在「节点可用性判定（字段组合）」「状态接口的坑（静默成功/回读校验）」「探测任务的节点门槛（isNodeNormal）」，属运维/调用方正确性知识，非纯文档速查。
