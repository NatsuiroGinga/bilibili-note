# 知识库关联检索摘要：vod-play / live-play 是怎么探测到的

## 问题

还有配置是 `vod-play` 和 `live-play`，这个是怎么探测到的？

## 检索结果

- **HTTP/ICMP/TCP 探测的真实执行方**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
  - 摘要：知识库内对六类探测（ICMP/SNMP/TCP/HTTP/Bandwidth/VodPlay/LivePlay）执行方的核查记录，2026-08-25 已用 noded 源码（`/Users/bilibili/Dev/bi`，`bvccdn-noded`）逐条确证。其中第 7、8 节专门核实 VodPlay/LivePlay 的探测机制与 URL 来源。这是本次问题的最直接命中文档。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md`

## 核心答案（noded 源码确证，2026-08-25）

**VodPlay/LivePlay 是六类探测中唯一用 ffmpeg 做真实拉流解码的探测类型**，与 HTTP/TCP 的"进程内纯 Go 网络调用"完全不同。

### 1. 探测执行方与执行机制（noded 侧）

- 执行方是 **miner 云主机**（执行探测的节点，如 `OSTHWEAST` 等 MinerChannel），不是被探测的 mcdn 节点本身。mcdn-v 节点因无 miner 能力、IDC 非 `01` 开头，根本进不了自探测代码路径。
- `task_runner.go:213-230` 的 `createVodPlayExecutor` / `createLivePlayExecutor` 创建同一个 `media.PlayExecutor`，只投递到 `vodPlayCh` / `livePlayCh` 两个 channel，执行逻辑完全一致，**没有区分点播/直播的分支**。
- `generateVodPlayEtorCfg` / `generateLivePlayEtorCfg`（`task_runner.go:320-338`）把 `pt.VodPlayURL` / `pt.LivePlayURL` 整段传给 `RemoteAddrs`——与 HTTP 同一种模式：**裸连配置的完整 URL，不读 `TargetIP`**。
- 真正拉流代码 `library/media/play.go:95-102` 的 `exec`：

  ```go
  // ffmpeg -user_agent -i ./test.mp4 -f rawvideo -y /dev/null
  err := ffmpeg.Input(mediaUrl, ffmpeg.KwArgs{"user_agent": "test"}).
      Output("/dev/null", ffmpeg.KwArgs{"format": "rawvideo"}).
      WithTimeout(timeout).OverWriteOutput().Run()
  ```

  即用 `u2takey/ffmpeg-go` 封装一次真实 ffmpeg 拉流：`-i <播放地址>` 输入，解码为 `rawvideo` 输出到 `/dev/null`。这是唯一**要求完整解封装+解码**的检测，比 HTTP 单次 GET、TCP 端口连通性严格得多。

- **反直觉的判定逻辑**：`err.Error() != "signal: killed"` 表示 **ffmpeg 因超时被杀不算失败**。超时杀进程时报的正是 `"signal: killed"`，被显式排除；只有 ffmpeg 提前主动报错终止（连不上、解码失败等）才判播放失败。即超时期间流只要一直在输出数据、没有提前中断，就视为播放成功。
- 同目录 `execCmd`（`play.go:104-114`）用 `os/exec` 直接调系统 ffmpeg，逻辑等价但 `//nolint:unused` 未被调用，是废弃/备用实现。

### 2. URL 从哪来（admin/ba 侧）

平台上的"vod 拨测"配置是一个 **bool 开关，不是 URL**（`ProbeConfig.VodPlay bool`，注释"是否开启 vod拨测"，`library/model/bo/probe_config.go:18`；LivePlay 同构）。

开关为 true 时才现算 URL，有三条互不相关的配置源，最终都落进同一个 `ProbeTask.VodPlay` 字段：

1. **Hebe 现算路径（`GenerateProbeTaskForMinerNoded`，probe.go:264-271）**：调 `GetVodPlayUrl`（`app/admin/internal/service/playurl.go:20-37`），先查 Redis 缓存（key `DialingTestVodPlayUrl:{nodeId}`，30 分钟过期），未命中则调 `hebe.GetVodPlayUrl(nodeId)` 并写回缓存；`GetLivePlayUrl` 结构相同。
2. **Hebe URL 生成带节点标识**：`hebe.GetVodPlayUrl`（`app/admin/internal/middleware/hebe/http_client.go:36-75`）调 Hebe 的 `VodUrlGenerate` 接口时把 **nodeId 作为 `cdnName`** 传入，生成形如 `{nodeId}.bilivideo.com` 的播放地址；`GetLivePlayUrl` 同理传 `cdn_info: nodeId`。即生成的 URL **意图指向这台节点**，与 HTTP 探测配任意第三方域名（如 baidu.com）语义上本质不同。
   - **未验证边界**：`{nodeId}.bilivideo.com` 是否真的被 CDN 调度解析/路由到对应节点，不在 ba/bi 仓库可读范围，是 Hebe/CDN 调度黑盒。知识库只证实"URL 携带节点标识"，未证实"请求真的打到这台节点"。
3. **人工配置路径（`GenerateProbeTaskForPcdnNoded`，probe.go:358-394）**：从 `s.dao.SelectDialingTaskMedia` 读取"拨测任务"配置表，按发起节点省份/运营商匹配，直接使用人工配置的 `task.DialingURL` 填入 `pt.VodPlay`/`pt.LivePlay`。这是业务方手动指定的固定拨测地址。

### 3. 六类探测全景对比

| 探测类型 | 连接目标 | 是否用 `TargetIP` | 实现方式 | 检测深度 |
| --- | --- | --- | --- | --- |
| ICMP / SNMP / TCP / Bandwidth | `pt.TargetIP` | 是 | 纯 Go 网络库 | 网络层/端口层 |
| HTTP | `pt.HTTP`（URL 列表） | 否 | 标准库 `http.Client.Get` | 单次 GET |
| VodPlay / LivePlay | `pt.VodPlayURL` / `pt.LivePlayURL` | 否 | 外部进程 ffmpeg 拉流解码 | 媒体流解封装+解码 |

VodPlay/LivePlay 是唯一动用外部进程、唯一做真实媒体解码验证的探测类型。

## 关联文档

- **出链（该文档引用谁）**：
  - `bban-api/Knowledge/bban-probe-task-api.md`（探测任务 API）
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md`（mcdn 探测目标）
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`（探测结果 prometheus exporter）
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md`
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md`（探测设计文档）
- **入链（谁引用该文档）**：`bban-api/Knowledge/bban-taishan-probe-mapping.md`（探测→泰山存储映射）、`bban-api/Knowledge/bban-node-status-silent-success.md`、`bban-api/Knowledge/bban-node-field-semantics.md`、`bban-api/Daily/2026-08-17.md` 等。
- **图扩展（depth=2，跨库相关）**：
  - `manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md`（MCDN vod 探测配置灰度上线，运维侧）
  - `manba-bi/Knowledge/mcdn-vod-forbidden-scheduling.md`（MCDN vod 禁调度）
  - `bban-api/Knowledge/bban-vod-reserve-gap.md`、`bban-api/Knowledge/bban-sid-lifecycle.md` 等

## 图谱提示

可在 Obsidian Graph View 查看可视化图谱：打开 `~/Dev/Research` vault，点左侧图谱图标，聚焦 `mcdn-v-probe-task-system` 节点即可看到上述关联网络。另可参考 `bban-api/Maps/bban-api-knowledge.canvas`。
