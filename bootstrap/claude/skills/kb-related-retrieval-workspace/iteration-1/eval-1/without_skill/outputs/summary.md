# mcdn 探测相关文档检索汇总（~/Dev/Research 知识库）

> 检索时间：2026-08-27 | 检索方式：research-knowledge MCP（knowledge_search，lexical/FTS5）+ 文件系统兜底检索
> 说明：FTS5 词法索引对中文短语命中有限，实际命中以文件系统检索为准（索引共 39 个文件）。

## 一、命中文档（直接相关，共 13 份）

### bban-api 知识库（BBAN 接口/鉴权/探测任务与结果查询，跨项目复用）

| # | 文档（Obsidian 跳转链接） | 路径 | 摘要 |
|---|---|---|---|
| 1 | [[mcdn-v-probe-task-system]] | `bban-api/Knowledge/mcdn-v-probe-task-system.md` | **核心文档**。mcdn-v 探测任务体系：候选池构建（isMcdnVodProbeTarget = IsMCDN + SID + service_type=="v"）、确定性抽样（sort 后前缀截断）、结果查询严格分派（读路径不容错、写路径降级）、类型判定短路优先级、pre 端到端验证。 |
| 2 | [[bban-mcdn-probe-targets]] | `bban-api/Knowledge/bban-mcdn-probe-targets.md` | BBAN 中 mcdn 探测目标与配置：人工配置方式、探测目标判定与 SID 关联限制。 |
| 3 | [[bban-probe-task-api]] | `bban-api/Knowledge/bban-probe-task-api.md` | BBAN 探测任务接口使用说明：路径映射、直连鉴权、返回语义。 |
| 4 | [[bban-taishan-probe-mapping]] | `bban-api/Knowledge/bban-taishan-probe-mapping.md` | 探测数据存储分布：Taishan `bban_probe_kv`（探测结果）/ `bban_misc_kv`（service_type），SCAN 查询方法、mcdn ID 格式。 |
| 5 | [[mcdn-probe-prometheus-exporter]] | `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` | 探测结果转 Prometheus 指标（mcdn_probe.py → `mcdn_probe_*` 指标），含跨运营商丢包 exporter 对照。 |
| 6 | [[bban-node-field-semantics]] | `bban-api/Knowledge/bban-node-field-semantics.md` | 节点字段语义（IsMCDN/Idc 前缀/SID），mcdn-v 探测目标判定与节点状态门槛（isNodeNormal）的依赖。 |
| 7 | [[bban-node-status-silent-success]] | `bban-api/Knowledge/bban-node-status-silent-success.md` | node-status 对不存在的 node_id 静默返回成功（探测/下线排查陷阱）。 |

### manba-bi 知识库（MCDN 踢点/下线运维）

| # | 文档（Obsidian 跳转链接） | 路径 | 摘要 |
|---|---|---|---|
| 8 | [[mcdn-vod-probe-config-rollout]] | `manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md` | MCDN VOD 探测配置批量发布（mcdn_probe_config_batch.py），复用 bban 签名机制与探测接口。 |
| 9 | [[mcdn-cross-isp-packet-loss]] | `manba-bi/Knowledge/mcdn-cross-isp-packet-loss.md` | MCDN 跨运营商丢包率（mcdn_network.sh 独立 exporter，Hawkeye datasource_id=74）。 |
| 10 | [[mcdn-promql-monitoring]] | `manba-bi/Knowledge/mcdn-promql-monitoring.md` | MCDN PromQL 监控查询方法（Hawkeye OpenAPI、数据源定位）。 |
| 11 | [[mcdn-vod-forbidden-scheduling]] | `manba-bi/Knowledge/mcdn-vod-forbidden-scheduling.md` | 点播禁用调度设计（脚本编排方案），与探测配置发布联动。 |

### 源头文档（Sources）

| # | 文档（Obsidian 跳转链接） | 路径 | 摘要 |
|---|---|---|---|
| 12 | [[et-bban-probe-design-docs]] | `bban-api/Sources/Docs/et-bban-probe-design-docs.md` | 探测设计源头文档，支撑 [[bban-mcdn-probe-targets]] 与 [[mcdn-v-probe-task-system]]。 |
| 13 | [[bban-api-evidence]] | `bban-api/Sources/Docs/bban-api-evidence.md` | 探测接口实测证据。 |

## 二、关联文档（间接相关）

| 文档（Obsidian 跳转链接） | 路径 | 关联点 |
|---|---|---|
| [[json-to-prometheus-textfile-workflow]] | `bban-api/Knowledge/` | 从 mcdn exporter 提炼的通用工作流，互相引用 |
| [[bban-sid-lifecycle]] | `bban-api/Knowledge/` | SID 生命周期，与探测目标 SID 关联限制互引 |
| [[bban-vod-reserve-gap]] | `bban-api/Knowledge/` | 点播储备带宽差额，与 SID/探测目标互引 |
| [[bban-signature-body-coverage]] | `bban-api/Knowledge/` | 探测配置批量发布复用的签名机制 |
| [[mcdn-设备交付全链路]] | `manba-bi/Knowledge/` | MCDN 设备交付全链路（含 [[Sources/Docs/mcdn-设备交付全链路-代码快照]]） |
| [[go-engineering-patterns]] | `manba-bi/Knowledge/` | 机器类型分流（BiliMcdnPrefix 前缀） |
| [[manba-bi-auto-online]] / [[manba-bi-fusing-protection]] / [[manba-bi-packet-loss-buffer]] | `manba-bi/Knowledge/` | MCDN 踢点/下线运维大主题下的自动上线、熔断保护、丢包缓冲 |
| 暂存（未提升，正式检索不可见） | `_ingestion-staging/20260827T161550+0800-mcdn-v-probe-port/` | 2026-08-27 mcdn-v 探测移植沉淀：`mcdn-v-probe-port-and-verification`、`probe-data-storage-and-taishan` 两份草稿，promotion 待 prod 端到端验证 |

## 三、核心关联网络

```
et-bban-probe-design-docs（源头设计）
        │ 支撑
        ▼
bban-mcdn-probe-targets（探测目标）◄──► bban-sid-lifecycle / bban-vod-reserve-gap
        │
        ▼
mcdn-v-probe-task-system（任务体系·核心）◄──► bban-probe-task-api（接口鉴权）
        │                                   ▲
        ├──► bban-taishan-probe-mapping（结果存储 Taishan bban_probe_kv）
        ├──► bban-node-field-semantics（节点字段/状态门槛）◄──► bban-node-status-silent-success
        └──► mcdn-probe-prometheus-exporter（指标出口）◄──► json-to-prometheus-textfile-workflow
                                          │
                                          ├──► mcdn-cross-isp-packet-loss（跨运营商丢包）
                                          └──► mcdn-promql-monitoring（监控查询）
mcdn-vod-probe-config-rollout（探测配置批量发布）──► bban-signature-body-coverage / mcdn-probe-prometheus-exporter
mcdn-vod-forbidden-scheduling（禁用调度）◄──► bban-node-field-semantics / bban-signature-body-coverage
```

## 四、跳转链接使用说明

- 以上均为 Obsidian wikilink（`[[文件名]]` 短链接），vault 为 `~/Dev/Research`，点击即可跳转。
- 若需 URI 形式：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system`。
- 入口：[[bban-api/00-Hub]]（bban-api 库）、[[manba-bi/00-Hub]]（manba-bi 库），总索引见 [[README]]。
