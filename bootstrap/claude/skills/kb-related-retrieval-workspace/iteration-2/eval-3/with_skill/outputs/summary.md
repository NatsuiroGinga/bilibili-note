# 知识库关联检索：bban-api node 状态

检索工具：research-knowledge MCP（`knowledge_search`，scope=`bban-api`；`knowledge_related`）
检索日期：2026-08-27
查询词：node 状态 / 节点状态 / 字段语义 / 静默成功 / taishan

> 说明：`lexical` 模式下中文多词查询为空（"node 状态"、"节点状态 node status taishan" 均无命中），
> 按 skill 提示改用 `mode="semantic"` 后命中质量显著提升（score 0.86-0.88），另用单关键词
> `node`、`status`、`静默`、`字段` 补充定位，并用 `knowledge_get` 兜底读取核心文档全文核验。

## 检索结果

- **bban-node-status-silent-success**（bban-api/Knowledge/bban-node-status-silent-success.md）
  - 摘要：`POST /v1/bban/node-status` 提交不存在的 node_id 时返回 `{"code":0,"data":"success"}` 静默成功不报错（2026-08-21 实测确认）。接口返回 success 不等于状态已变更。危害两层：假成功（BBAN 的 id 与 hostname 是不同字段，误用 hostname 提交会返回 success 但一台节点都没改）+ 绕过熔断（未知 id 落在 others 分支，不参与 McdnFuseCheck 熔断计数）。调用方必须回读 BBAN schedule 按 id 比对状态校验。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success.md)

- **bban-node-field-semantics**（bban-api/Knowledge/bban-node-field-semantics.md）
  - 摘要：BBAN 节点可用性无全局统一规则。`vod-play.can/status/frozen`、节点 `status/health`、`ipisps.forbidden` 在不同代码路径组合方式完全不同。列出三个场景实际判定谓词（标签熔断容量计数 `HasAbility+NodeAvailable+AbilityAvailable`；点播 MCDN 调度 `CheckAbility`+Status==Normal+Health==normal；逻辑交换机容量累计不过滤）。能力检查函数精确语义：`CheckAbility=Can&&!Frozen`，`AbilityAvailable=Can&&!Frozen&&RtStatus`，`HasAbility=只看标签存在`。附五个字段业务含义与"配置拨测 ≠ 参与调度"的注意。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md)

- **mcdn-v-probe-task-system**（bban-api/Knowledge/mcdn-v-probe-task-system.md）
  - 摘要：mcdn-v 探测任务系统全景，含多处 node 状态相关判断：`GenerateSimplifyTask` prod 环境 + 节点状态非正常返回空任务；`isNodeNormal` 节点状态门槛；mcdn-v 目标判定链、候选池抽样、结果查询容错不对称、noded 职责与执行边界、pre 环境运行验证与待验证项。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md)

- **bban-taishan-probe-mapping**（bban-api/Knowledge/bban-taishan-probe-mapping.md）
  - 摘要：节点相关数据（service_type、探测结果）的存储分布与读写源由配置开关决定：Taishan（`bban_misc_kv` / `bban_probe_kv`，key `{bban2_probe_result:<nodeID>}$<type>$<source>`）或 Redis 兜底；含 Taishan SCAN 查询方法。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md)

## 关联文档

- 出链（node 状态文档引用谁）：
  - bban-node-status-silent-success → bban-node-field-semantics ×1、mcdn-v-probe-task-system ×1
  - bban-node-field-semantics → bban-node-status-silent-success ×1、mcdn-v-probe-task-system ×1
- 入链（谁引用 node 状态文档）：
  - 两者共同被 mcdn-v-probe-task-system ×N 引用（mcdn-v 探测的节点状态判断 / isNodeNormal）
  - 导航文件：00-Hub.md、02-Index.md、01-Plan.md、_system/registry.md、Daily/2026-08-17.md
- 图扩展（depth=2，从 mcdn-v-probe-task-system BFS）：
  - Knowledge/（有沉淀价值）：bban-probe-task-api、bban-mcdn-probe-targets、bban-node-field-semantics、bban-node-status-silent-success、bban-sid-lifecycle、bban-signature-body-coverage、bban-taishan-probe-mapping、bban-vod-reserve-gap、json-to-prometheus-textfile-workflow、mcdn-probe-prometheus-exporter
  - Sources/Docs/（证据源）：bban-api-evidence、et-bban-probe-design-docs、hawkeye-prometheus-openapi、hawkeye-prometheus-datasource-query、moni-http-client-metric-cardinality
  - 跨项目（manba-bi，MCDN 运维侧）：Daily/2026-08-21、Knowledge/mcdn-cross-isp-packet-loss、Knowledge/mcdn-promql-monitoring、Knowledge/mcdn-vod-forbidden-scheduling、Knowledge/mcdn-vod-probe-config-rollout

## 图谱提示

node 状态主题的关联网络以 **bban-node-status-silent-success ↔ bban-node-field-semantics** 为双核，
两篇文档互相出链/入链，并共同挂接在 mcdn-v-probe-task-system 上；向外辐射到探测任务 API、探针目标、
Taishan 存储映射（bban 探测链路），以及跨项目 manba-bi 的 MCDN 调度运维（踢点/下线/丢包/监控）。
可在 Obsidian Graph View 打开 ~/Dev/Research vault 查看可视化图谱；图谱 canvas 见
`bban-api/Maps/bban-api-knowledge.canvas`。
