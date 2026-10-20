# 知识库关联检索结果：云主机探测 mcdn 的任务配置 / miner 云主机探测执行方

> 检索范围：`research-knowledge` MCP `knowledge_search`，scope=`bban-api`（lexical 中文多词为空，semantic 中文查询命中），并顺带检查 `manba-bi` 库补充。

## 结论（直接回答）

**有相关参考，且覆盖度很高。** 知识库 `bban-api` 库已沉淀一套完整的 mcdn-v 探测任务体系笔记，直接回答了"云主机探测 mcdn 的任务配置"与"miner 是云主机探测执行方"两个问题：

- **任务配置**：mcdn 探测配置由管理员手工维护，配置键用 **BA 节点 ID**（不能用北斗主机名）；常见配置项为 ICMP、TCP 端口、HTTP 地址、SNMP、带宽网卡及播放地址；"vod 拨测"是平台上的一个 bool 开关（`ProbeConfig.VodPlay`），开启后由 admin 现算播放 URL（Hebe `VodUrlGenerate`，cdnName=nodeId），另有独立的"拨测任务配置表"可人工指定固定拨测 URL（`DialingURL`）。
- **miner 云主机探测执行方**：实际发起 HTTP/ICMP/TCP 探测的是 **miner 云主机**（paladin 配置 `minerProbePercentage` 配了 8 台云主机，命名如 `tx-bj-video-ost-miner-1`、`hw-sz-video-ost-miner-1`、`ali-cd-video-ost-miner-1`），由带 `miner` 能力的 noded 领取批量目标探测任务执行；探测结果 `Source` 字段记录 miner 的 `MinerChannel`（如 `OSTHWEAST`）；HTTP 探测裸连配置的完整 URL，与目标节点 `TargetIP` 完全无关（noded 源码已确证）。
- **任务生成链路**：候选池由 `isMcdnVodProbeTarget`（`IsMCDN()` + SID + `service_type=="v"`）构建，miner 实际任务由 `minerProbePercentage` 确定性抽样产生（`sort.Strings` 后前缀截断），候选任务 ≠ miner 实际任务。

## 检索结果

- **mcdn-v-probe-task-system**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
  - 摘要：mcdn-v 探测任务分三层——候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建，miner 实际任务由 `percentage` 确定性抽样产生，结果查询用独立的 `generateNodeProbeTaskForResult` 严格分派；已用 noded 源码确证 HTTP/ICMP/TCP 探测的真实执行方是 miner 云主机（HTTP 裸连 URL、与 TargetIP 无关）；含 `ProbeConfig` 字段定义、VodPlay/LivePlay 开关与 URL 现算逻辑、六类探测全景对比。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md)

- **bban-mcdn-probe-targets**（`bban-api/Knowledge/bban-mcdn-probe-targets.md`）
  - 摘要：mcdn 探测目标与配置——配置键用 BA 节点 ID、管理员手工维护、常见配置项（ICMP/TCP/HTTP/SNMP/带宽/播放地址）；目标判定顺序：北斗同步 service_type（点播用 "v"）→ 人工探测配置 → 可用目标 IP；候选池不以在线/离线为条件，实际连通性由 miner 执行探测后以结果体现。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md)

- **bban-probe-task-api**（`bban-api/Knowledge/bban-probe-task-api.md`）
  - 摘要：BBAN 探测任务接口使用说明——查询候选探测池用已签名 SLB 接口 `/api/bban2/v1/all-probe-task` 并精确匹配节点 ID；命中返回目标 IP 与 ICMP/SNMP/TCP/HTTP/带宽等探测配置；不要把候选池当作 miner 实际任务（实际任务受 `minerProbePercentage` 影响）。
  - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md)

## 关联文档

- 出链（核心文档引用谁）：`bban-probe-task-api`、`bban-mcdn-probe-targets`、`et-bban-probe-design-docs`（Sources）、`mcdn-probe-prometheus-exporter`、`json-to-prometheus-textfile-workflow`
- 入链（谁引用核心文档）：`00-Hub`、`02-Index`、`01-Plan`、`_system/registry`、`Daily/2026-08-17`、`bban-node-status-silent-success`、`bban-node-field-semantics`、`bban-taishan-probe-mapping`、`mcdn-probe-prometheus-exporter`、`bban-mcdn-probe-targets`、`json-to-prometheus-textfile-workflow`、`et-bban-probe-design-docs`
- 次级关联：`bban-vod-reserve-gap`、`bban-sid-lifecycle`（SID 身份关联，来自 bban-mcdn-probe-targets 入链）；`bban-taishan-probe-mapping`（泰山 service_type 映射）
- manba-bi 旁路补充（非探测任务本身，但相关）：`mcdn-设备交付全链路`（北斗资源同步，是候选池 SID→service_type 的上游来源）、`mcdn-promql-monitoring`（mcdn_network_quality 监控数据源）

## 图谱提示

可在 Obsidian Graph View 中查看 `~/Dev/Research` vault 的关联图谱；`bban-api` 库另有 `bban-api/Maps/bban-api-knowledge.canvas` 画布可直观查看探测任务主题下的文档网络。

## 使用建议

新需求"云主机探测 mcdn 任务配置"可直接以 `bban-api/Knowledge/mcdn-v-probe-task-system.md` 为基准笔记，其内已含代码位置（`ba` 仓库 `app/admin/internal/service/probe.go`、`library/model/bo/probe_config.go`，`bi` 仓库 `library/probe/task_runner.go` 等）与置信度标注，可直接引用结论，无需重复调研。
