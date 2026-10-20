# bban-api 知识库「node 状态」关联检索汇总

> 检索方式：research-knowledge MCP `knowledge_search`（lexical 模式，中文分词命中为空，按 skill 降级）→ Obsidian CLI `search` 全文检索兜底（vault=Research）→ `links`/`backlinks` 提取出链/入链。
> 生成时间：2026-08-27

## 检索结果（命中文档，按相关性排序）

- **bban-node-status-silent-success**（bban-api/Knowledge/bban-node-status-silent-success.md）
  - 摘要：`POST /v1/bban/node-status` 提交不存在的 node_id 时静默返回 success（不报错不提示）。未知 id 经 `SplitByNodeType` 落入 others 分支，绕过 MCDN 熔断检查；调用方不能以接口返回值作为生效依据，必须回读 BBAN schedule 按 id 比对状态，区分三种回读结果（已变更/缓存延迟/无效标识）。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-status-silent-success`

- **bban-node-field-semantics**（bban-api/Knowledge/bban-node-field-semantics.md）
  - 摘要：BBAN「节点能不能用」没有全局统一规则。`vod-play.can/status/frozen`、节点 `status/health`、`ipisps.forbidden` 在不同代码路径（标签熔断容量计数、点播 MCDN 调度输出 GetVodMcdnNode、逻辑交换机容量累计 CalcBizBw）组合方式完全不同，并给出 CheckAbility/AbilityAvailable/HasAbility 三个能力检查函数的精确语义。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics`

- **mcdn-v-probe-task-system**（bban-api/Knowledge/mcdn-v-probe-task-system.md）
  - 摘要：mcdn-v 探测任务三层体系（候选池 isMcdnVodProbeTarget → percentage 确定性抽样 → 结果查询严格分派，读路径不容错、写路径降级）。其中与 node 状态直接相关的门槛：`GenerateSimplifyTask` 在 prod 环境用 `isNodeNormal(fromNode)` 判断节点状态非正常则返回空任务。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system`

## 关联文档

### bban-node-status-silent-success
- 出链（它引用谁）：bban-node-field-semantics ×1、mcdn-v-probe-task-system ×1
- 入链（谁引用它）：bban-node-field-semantics、bban-signature-body-coverage、_system/registry、Maps/bban-api-knowledge.canvas、manba-bi/Daily/2026-08-21、manba-bi/Knowledge/mcdn-vod-forbidden-scheduling

### bban-node-field-semantics
- 出链：bban-node-status-silent-success ×1、mcdn-v-probe-task-system ×1
- 入链：bban-node-status-silent-success、_system/registry、Maps/bban-api-knowledge.canvas、manba-bi/Knowledge/mcdn-vod-forbidden-scheduling、manba-bi/Knowledge/mcdn-vod-probe-config-rollout

### mcdn-v-probe-task-system（hub 级条目，关联最广）
- 出链：bban-mcdn-probe-targets、bban-probe-task-api、json-to-prometheus-textfile-workflow、mcdn-probe-prometheus-exporter、Sources/Docs/et-bban-probe-design-docs
- 入链：bban-node-field-semantics、bban-node-status-silent-success、bban-mcdn-probe-targets、bban-taishan-probe-mapping、json-to-prometheus-textfile-workflow、mcdn-probe-prometheus-exporter、Sources/Docs/et-bban-probe-design-docs、00-Hub、01-Plan、02-Index、Daily/2026-08-17、Maps/bban-api-knowledge.canvas、_system/registry

### 关联主题归纳（出链/入链聚合）

| 主题 | 文档 |
| --- | --- |
| 节点可用性判定（核心） | bban-node-field-semantics、bban-node-status-silent-success、mcdn-v-probe-task-system（isNodeNormal） |
| 探测任务与目标 | bban-probe-task-api、bban-mcdn-probe-targets、bban-taishan-probe-mapping、Sources/Docs/et-bban-probe-design-docs |
| 鉴权 | bban-signature-body-coverage（node-status 401 根因） |
| 指标导出 | mcdn-probe-prometheus-exporter、json-to-prometheus-textfile-workflow |
| 跨项目运维（manba-bi） | mcdn-vod-forbidden-scheduling（按丢包率禁用调度）、mcdn-vod-probe-config-rollout（批量配置探测灰度）、Daily/2026-08-21（首次实测记录） |
| 其他同库条目 | bban-sid-lifecycle、bban-vod-reserve-gap（SID/储备带宽，弱关联） |

## 图谱提示

可在 Obsidian Graph View 中查看可视化图谱：打开 `~/Dev/Research` vault（名称 Research），点击左侧图谱图标；或直接打开 `bban-api/Maps/bban-api-knowledge.canvas` 查看 bban-api 知识图谱。
