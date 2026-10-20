# bban-api 知识库「node 状态」主题检索汇总（baseline，由子代理返回文本转存）

## 一、命中文档（node 状态直接相关，2 篇）

1. **bban-node-status-silent-success.md**（knowledge-005）— 标题「node-status 对不存在的 node_id 静默返回成功」。实测 `POST /v1/bban/node-status` 提交不存在的 node_id 返回 `{"code":0,"message":"0","ttl":1,"data":"success"}`。两层危害：假成功（id 与 hostname 字段不同）；绕过熔断。调用方必须回读 BBAN schedule 按 id 比对状态，区分「已变更/缓存延迟/id 不存在」三种结果。
2. **bban-node-field-semantics.md**（knowledge-008）— 标题「BBAN 节点可用性字段的场景化语义」。节点可用性无全局统一规则：标签熔断用 `HasAbility+NodeAvailable+AbilityAvailable`；点播 MCDN 调度用 `CheckAbility+Status==Normal+Health==normal`；逻辑交换机容量累计无状态过滤。

## 二、关联文档（wikilink 直接互链，2 篇）

3. **mcdn-v-probe-task-system.md**（knowledge-003）— 两篇 node 状态文档均引用，含 `isNodeNormal` 状态门槛。
4. **bban-signature-body-coverage.md**（knowledge-004）— 以 node-status 为实测样例，连接「node 状态」与「鉴权」主题。

## 三、扩展主题网络

| 主题 | 文档 |
| --- | --- |
| 探测任务 | bban-probe-task-api、bban-mcdn-probe-targets、bban-taishan-probe-mapping |
| 指标监控 | mcdn-probe-prometheus-exporter、json-to-prometheus-textfile-workflow |
| SID/带宽 | bban-sid-lifecycle、bban-vod-reserve-gap |
| 证据来源 | Sources/Docs/bban-api-evidence、et-bban-probe-design-docs |

入口：bban-api/00-Hub.md、02-Index.md、_system/registry.md。

## 四、跳转链接

`[[Knowledge/bban-node-status-silent-success]]`、`[[Knowledge/bban-node-field-semantics]]`、`[[Knowledge/mcdn-v-probe-task-system]]`、`[[Knowledge/bban-signature-body-coverage]]`、`[[Knowledge/bban-probe-task-api]]`、`[[Knowledge/bban-mcdn-probe-targets]]`、`[[Knowledge/bban-taishan-probe-mapping]]`、`[[Sources/Docs/bban-api-evidence]]`、`[[Sources/Docs/et-bban-probe-design-docs]]`

（注：baseline 无 skill 指导，输出用 wikilink 而非 obsidian:// 链接）
