# 检索结果汇总：vod-play / live-play 是怎么探测到的

## 检索来源

- 知识库：`~/Dev/Research`（Obsidian vault，索引 40 个文件）
- 命中核心文档：`bban-api/Knowledge/mcdn-v-probe-task-system.md`（已用 noded 源码确证，2026-08-25）
- 关联文档：`bban-api/Knowledge/bban-probe-task-api.md`、`bban-api/Knowledge/bban-mcdn-probe-targets.md`、`bban-api/Sources/Docs/et-bban-probe-design-docs.md`

## 核心结论

**平台上的 `vod-play`/`live-play` 是布尔开关，不是 URL；开启后 URL 由 admin 现算，真正执行探测的是 noded 侧的 miner，用外部进程 ffmpeg 做真实拉流解码。**

### 1. 配置形态：开关（bool）

- `ProbeConfig.VodPlay bool`（`library/model/bo/probe_config.go:18`，注释"是否开启 vod 拨测"），LivePlay 同构。
- 配置本身不含 URL，URL 在生成 `ProbeTask` 时现算。

### 2. URL 来源（三条独立路径）

- **路径一/二（开关 + Hebe 现算）**：`GenerateProbeTaskForMinerNoded`（probe.go:264-271）与 `GenerateProbeTaskForPcdnNoded`（probe.go:338-345）当开关为 true 时调 `GetVodPlayUrl`/`GetLivePlayUrl`（`app/admin/internal/service/playurl.go:20-37 / 39-56`）：
  - 先查 Redis 缓存（key `DialingTestVodPlayUrl:{nodeId}`，30 分钟过期），未命中则调 Hebe 的 `VodUrlGenerate`/`LiveUrlGenerate`，拿回后写回缓存。
  - Hebe 请求把 **nodeId 作为参数**传入：Vod 用 `cdnName: {nodeId}.bilivideo.com`，Live 用 `cdn_info: nodeId`（`app/admin/internal/middleware/hebe/http_client.go:36-75+`）。生成的播放 URL **携带节点标识、意图指向这台节点**，与 HTTP 探测配置任意第三方域名（如 baidu.com）语义本质不同。
  - 未验证边界：域名是否真的被 CDN 调度路由到该节点，属 Hebe/CDN 调度黑盒，`ba`/`bi` 仓库无法证实。
- **路径三（人工拨测任务表）**：`GenerateProbeTaskForPcdnNoded`（probe.go:358-394）从 `SelectDialingTaskMedia` 配置表读取人工指定的 `DialingURL`，按拨测发起节点的省份/运营商匹配后填入 `pt.VodPlay`/`pt.LivePlay`。与前两条互不相关，只是最终落进同一个字段。

### 3. 探测执行方式（noded 源码确证）

- `createVodPlayExecutor`/`createLivePlayExecutor`（task_runner.go:213-230）创建同一个 `media.PlayExecutor`，仅分别投递到 `defaultSender.vodPlayCh` / `defaultSender.livePlayCh` 两个 channel，逻辑完全一致。
- `generateVodPlayEtorCfg`/`generateLivePlayEtorCfg`（task_runner.go:320-338）把整段 URL 传给 `RemoteAddrs`，**裸连 URL、不读 TargetIP**（与 HTTP 探测同一种模式）。
- 真实执行在 `library/media/play.go:95-102`：用 `github.com/u2takey/ffmpeg-go` 跑真实 ffmpeg 拉流 `ffmpeg -user_agent test -i <播放地址> -f rawvideo -y /dev/null`，要求**完整解封装 + 解码**。
- 这是六类探测里**唯一动用外部进程、唯一做真实媒体解码验证**的类型；其余五类（ICMP/SNMP/TCP/Bandwidth/HTTP）都是进程内纯 Go 网络调用。
- **反直觉判定**：ffmpeg 因超时被杀（`err == "signal: killed"`）**不算失败**，显式排除在错误判定之外；只有 ffmpeg 提前主动报错（连不上、解码失败等）才判定播放失败。
- 另有一个等价但 `//nolint:unused` 标注的废弃实现 `execCmd`（os/exec 直调系统 ffmpeg，play.go:104-114）。

### 4. 执行方身份与结果记录

- 真正发起探测的是执行该任务的 miner 云主机，mcdn-v 节点自身无自探测入口（`GET /task` 需 `IsNCDN() || CheckAbility("miner")`，mcdn-v 节点均不满足）。
- 结果按 `TargetNodeID` 打标签存储，`Source` 字段记录 miner 的 `MinerChannel`（如 `OSTHWEAST`），两者是不同维度。
- **结果读取注意**：`ProbeResultSet` 只暴露 ICMP/SNMP/TCP/HTTP/Bandwidth，**不含 `vod_play`/`live_play`**，`/all-probe-result` 接口无法判断点播结果是否写入（pre 环境运行验证 2026-08-17 佐证）。

## 证据置信度

- 配置字段、URL 生成、Hebe 参数、noded 执行逻辑、ffmpeg 命令与判定：均为**代码确证**。
- 域名是否路由到目标节点：**未验证边界**（Hebe/CDN 调度黑盒）。

## 关键文件路径

- `library/model/bo/probe.go:16-27`（ProbeTask 结构体，含 `VodPlay`/`LivePlay` 字段）
- `library/model/bo/probe_config.go:18`（VodPlay 开关定义）
- `app/admin/internal/service/playurl.go`（GetVodPlayUrl / GetLivePlayUrl + Redis 缓存）
- `app/admin/internal/middleware/hebe/http_client.go`（Hebe VodUrlGenerate/LiveUrlGenerate，cdnName=nodeId）
- `library/probe/task_runner.go:213-338`（createVodPlayExecutor/createLivePlayExecutor + generateVodPlayEtorCfg/generateLivePlayEtorCfg）
- `library/media/play.go:95-114`（ffmpeg 拉流解码 exec）

## Obsidian 跳转链接

- 核心文档：obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md
- 关联：bban-api/Knowledge/bban-probe-task-api.md、bban-api/Knowledge/bban-mcdn-probe-targets.md、bban-api/Sources/Docs/et-bban-probe-design-docs.md
