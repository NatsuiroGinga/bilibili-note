# 知识库检索结果汇总：mcdn 探测移植

## 检索方式

- 工具：`research-knowledge` MCP，`knowledge_search`（lexical 模式，生产默认）
- 检索词：`mcdn 探测移植`、`mcdn 探测`、`探测迁移`、`mcdn 探测任务 移植 v 节点`、`mcdn 探测 迁移 泰山`、`mcdn probe task migrate`、`mcdn`、`探测` 等
- 命中库：**bban-api**（BBAN 接口、鉴权、探测任务与结果查询，跨项目复用）；检索词「mcdn 探测移植」「探测迁移」等组合词未直接命中，最相关沉淀在 `bban-api/Knowledge/` 下的 mcdn 探测系列条目中。

## 命中的核心条目（按相关度排序）

| 条目 | 内容要点 | Obsidian 链接 |
| --- | --- | --- |
| `bban-api/Knowledge/mcdn-v-probe-task-system.md`（主条目） | mcdn-v 探测任务三层体系：候选池、确定性抽样、结果查询分派；目标判定链；noded 执行边界；泰山存储映射；发布影响 | obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md |
| `bban-api/Knowledge/bban-mcdn-probe-targets.md` | mcdn 探测目标判定：先看北斗同步的 service_type，再看人工配置和目标 IP，不看主机名字面形式；SID 身份关联限制 | obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md |
| `bban-api/Knowledge/bban-probe-task-api.md` | 探测任务接口：查询候选池用已签名 SLB `/api/bban2/v1/all-probe-task`，精确匹配节点 ID | obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md |
| `bban-api/Knowledge/bban-taishan-probe-mapping.md` | 泰山 service_type 映射：`bban_misc_kv` 存 service_type，`bban_probe_kv` 存探测结果（V2 key）；SCAN 替代 hgetall | obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md |
| `bban-api/Sources/Docs/et-bban-probe-design-docs.md` | 设计文档来源：原始文档为 et 的 `ncdn-mcdn-v-probe-migration-design` 等，归纳出目标判定、配置绑定、SID 关联等可复用事实 | obsidian://open?vault=Research&file=bban-api/Sources/Docs/et-bban-probe-design-docs.md |
| `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` / `json-to-prometheus-textfile-workflow.md` | 探测结果转 Prometheus 指标的下游链路 | 见主条目关联 |

## 关键知识摘要（mcdn 探测移植的核心结论）

### 1. 任务体系三层结构（主条目「一句话结论」）
- 候选池：由 `isMcdnVodProbeTarget` 构建，条件 = `IsMCDN()`（node ID 前缀 "mcdn"）+ SID 解析成功 + `service_type=="v"`（点播）。
- miner 实际任务：`GenerateProbeTaskForMinerNoded(percentage)` 对节点+交换机合并集合做**确定性抽样**（`sort.Strings` 后取前缀 `ceil(len*percentage/100)`），非随机；`percentage=100` 返回全量。
- 结果查询：独立分派 `generateNodeProbeTaskForResult`，**容错不对称**——下发路径对泰山查询失败降级跳过，结果查询路径严格报错不降级（读路径不容错、写路径降级）。

### 2. 目标判定链（代码级确认）
mcdn-v 节点 ID 格式 `mcdn-<x>-<x>-<isp>-<sid>`（5 段），SID = 第 5 段；service_type 取值集 `"v"`（点播）/`"live"`（直播）/`"bvcmix"`（混跑），只有 `"v"` 进候选池。映射来自 `QueryAllPortalServiceTypeFromTaishan`。防御性编程：精确类型判定（`IsMCDN`）必须先于字段启发式（`HasPrefix(Idc,"01")`），否则新类型被旧分支误吞（d937be77 已修复的 bug）。

### 3. 探测执行方边界（2026-08-25 noded 源码确证）
- mcdn-v 节点自身**无自探测代码入口**（判定恒为 false，无 miner 能力、Idc 均以 "03" 开头）。
- 实际发起探测的是 miner 云主机。HTTP/VodPlay/LivePlay 探测**裸连配置的完整 URL，与 TargetIP 完全无关**；ICMP/SNMP/TCP/Bandwidth 才连 TargetIP。
- VodPlay/LivePlay 是唯一用 ffmpeg 做真实解封装+解码的探测；URL 由 admin 现算（hebe 接口传 nodeId 生成 `{nodeId}.bilivideo.com` 播放地址），或读人工配置的拨测表。
- 结果存储 key = `(TargetNodeID, url)`，`Source` 字段记录真正执行的 miner 渠道（如 `OSTHWEAST`），两维度分开。

### 4. 存储与配置映射
- 读写源由配置开关决定：`serviceFromTaishan`/`qosFromTaishan`=true 走 Taishan（service_type 在 `bban_misc_kv`，探测结果在 `bban_probe_kv`），false 走 Redis。
- 探测配置存 MySQL `bban_probe_config`（node_id + dtime=0），节点存 `bban_node`。配置键用 BA 节点 ID，不能用北斗主机名。
- 泰山无原生 HGETALL，ba 用 SCAN（KeyPrefix=hashKey，单次 1000 分页）实现。

### 5. 发布与验证边界（2026-08-27）
- `SyncMCDNResourceFromPortal` cron 非 prod 不执行；mcdn 节点的 noded 连 prod admin，**端到端验证需 prod admin 发布**后才生效。
- pre 环境验证范围仅限单元测试 + `curl /v0/all-probe-task`（已有节点命中实证：mcdn-ydy-sxxa-ct-50059223 精确命中并生成 TCP/HTTP/点播任务，但结果查询为空）。
- `ProbeResultSet` 只暴露 ICMP/SNMP/TCP/HTTP/Bandwidth，不含 vod_play/live_play，`/all-probe-result` 不能判断点播结果。

### 6. 待验证事项（来自主条目）
- 生产环境 mcdn 节点 Idc 实际取值分布。
- `QueryAllPortalServiceTypeFromTaishan` 的缓存键与刷新周期。
- noded 仓库的 ICMP/TCP/SNMP/Bandwidth 执行细节与完整任务领取/上报周期。
- ffmpeg 拉流探测的资源开销（每 URL 一个子进程，60 秒一轮）。
- `{nodeId}.bilivideo.com` 是否真的被 CDN 调度路由到对应节点（Hebe 侧黑盒）。

## 关联与跳转（可扩展阅读）

- 上游/关联知识：`bban-sid-lifecycle`、`bban-vod-reserve-gap`（SID 生命周期与点播储备带宽差额）
- 证据来源：`Sources/Docs/bban-api-evidence.md`、`Sources/Docs/et-bban-probe-design-docs.md`
- 入口：`bban-api/00-Hub.md`（最近更新/当前焦点/当前问题）、`bban-api/02-Index.md`、`bban-api/01-Plan.md`（待办）
- 项目库总索引：`Research/README.md`（bban-api / manba-bi / te 三个项目分库）

## 检索结论

知识库对「mcdn 探测移植」已有**体系化沉淀**（主条目 `mcdn-v-probe-task-system` 为 2026-08-27 更新，含源码级证据），覆盖从设计文档（et）→ 目标判定 → 候选池/抽样 → 结果查询 → noded 执行 → 泰山存储 → 发布影响的完整链路，并明确标注了待验证边界。本次任务可直接复用这些结论，无需重新调研。
